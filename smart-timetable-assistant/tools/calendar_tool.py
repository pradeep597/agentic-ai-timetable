from langchain.tools import tool
from database.db import get_connection
from datetime import datetime, timedelta
import pytz

# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(s: str) -> datetime:
    """Accept 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD HH:MM:SS'."""
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Cannot parse datetime: {s!r}")


def _save_event_local(title, description, start_time, end_time,
                      event_type="class", google_event_id=None):
    conn = get_connection()
    conn.execute(
        """INSERT INTO events
           (title, description, start_time, end_time, event_type, google_event_id)
           VALUES (?,?,?,?,?,?)""",
        (title, description, start_time, end_time, event_type, google_event_id),
    )
    conn.commit()
    conn.close()


# ── tools ─────────────────────────────────────────────────────────────────────

@tool
def create_event(title: str, start_time: str, end_time: str,
                 description: str = "", event_type: str = "class") -> str:
    """Create a new scheduled event and save it locally.
    start_time / end_time format: 'YYYY-MM-DD HH:MM'.
    event_type options: class | exam | study | lab | other."""
    try:
        # Validate times parse correctly
        _parse_dt(start_time)
        _parse_dt(end_time)

        # Try Google Calendar sync — silently skip if not configured
        google_event_id = None
        try:
            from utils.auth import get_google_credentials
            from googleapiclient.discovery import build
            ist = pytz.timezone("Asia/Kolkata")
            creds = get_google_credentials()
            service = build("calendar", "v3", credentials=creds)
            start_dt = ist.localize(_parse_dt(start_time))
            end_dt = ist.localize(_parse_dt(end_time))
            body = {
                "summary": title,
                "description": description,
                "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Kolkata"},
                "end":   {"dateTime": end_dt.isoformat(),   "timeZone": "Asia/Kolkata"},
            }
            result = service.events().insert(calendarId="primary", body=body).execute()
            google_event_id = result.get("id")
        except Exception:
            pass  # No credentials.json — local-only mode

        _save_event_local(title, description, start_time, end_time,
                          event_type, google_event_id)

        sync_note = " (also synced to Google Calendar ✅)" if google_event_id else " (saved locally)"
        return (f"✅ **{title}** scheduled from {start_time} to {end_time}"
                f" [{event_type}]{sync_note}")
    except Exception as e:
        return f"❌ Could not create event: {e}"


@tool
def get_events(date: str) -> str:
    """Get all events for a specific date. Format: 'YYYY-MM-DD'."""
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT title, start_time, end_time, event_type FROM events "
            "WHERE start_time LIKE ? ORDER BY start_time",
            (f"{date}%",),
        ).fetchall()
        conn.close()

        if not rows:
            return f"📭 No events found for {date}."

        lines = [f"📅 Events on **{date}**:"]
        type_emoji = {"class": "📖", "exam": "📝", "study": "📚", "lab": "🔬", "other": "📌"}
        for r in rows:
            emoji = type_emoji.get(r["event_type"], "📌")
            lines.append(f"  {emoji} **{r['title']}** — {r['start_time'][11:16]} → {r['end_time'][11:16]}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Error fetching events: {e}"


@tool
def find_free_slots(date: str, duration_minutes: int = 60) -> str:
    """Find available free time slots on a given date for a specified duration.
    date format: 'YYYY-MM-DD'. duration_minutes: integer (e.g. 60, 90, 120)."""
    try:
        conn = get_connection()
        rows = conn.execute(
            "SELECT start_time, end_time FROM events WHERE start_time LIKE ? ORDER BY start_time",
            (f"{date}%",),
        ).fetchall()
        conn.close()

        work_start = datetime.strptime(f"{date} 08:00", "%Y-%m-%d %H:%M")
        work_end   = datetime.strptime(f"{date} 22:00", "%Y-%m-%d %H:%M")
        busy = []
        for r in rows:
            try:
                busy.append((_parse_dt(r["start_time"]), _parse_dt(r["end_time"])))
            except ValueError:
                pass

        free = []
        current = work_start
        for s, e in sorted(busy):
            if current + timedelta(minutes=duration_minutes) <= s:
                free.append(f"  🕐 {current.strftime('%I:%M %p')} – {s.strftime('%I:%M %p')}")
            current = max(current, e)
        if current + timedelta(minutes=duration_minutes) <= work_end:
            free.append(f"  🕐 {current.strftime('%I:%M %p')} – {work_end.strftime('%I:%M %p')}")

        if not free:
            return f"😔 No free slots of {duration_minutes} min found on {date}."
        return f"✅ Free slots of ≥{duration_minutes} min on **{date}**:\n" + "\n".join(free)
    except Exception as e:
        return f"❌ Error finding slots: {e}"
