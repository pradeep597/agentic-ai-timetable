from langchain.tools import tool
from database.db import get_connection
from datetime import datetime, timedelta

# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_dt(s: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            pass
    raise ValueError(f"Cannot parse datetime: {s!r}")

PRIORITY_EMOJI = {"high": "🔴", "medium": "🟡", "low": "🟢"}

# ── tools ─────────────────────────────────────────────────────────────────────

@tool
def check_conflict(start_time: str, end_time: str) -> str:
    """Check whether a proposed time slot overlaps with any existing event.
    start_time / end_time format: 'YYYY-MM-DD HH:MM'."""
    try:
        conn = get_connection()
        conflicts = conn.execute(
            """SELECT title, start_time, end_time FROM events
               WHERE NOT (end_time <= ? OR start_time >= ?)""",
            (start_time, end_time),
        ).fetchall()
        conn.close()

        if not conflicts:
            return "✅ Time slot is free — no conflicts found!"

        lines = ["⚠️ **Conflicts detected:**"]
        for c in conflicts:
            lines.append(f"  • **{c['title']}** ({c['start_time'][11:16]} – {c['end_time'][11:16]})")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Conflict check error: {e}"


@tool
def add_assignment(title: str, subject: str, deadline: str,
                   priority: str = "medium") -> str:
    """Add an assignment with a deadline. 
    deadline format: 'YYYY-MM-DD HH:MM'. 
    priority: 'high' | 'medium' | 'low'."""
    try:
        priority = priority.lower()
        if priority not in ("high", "medium", "low"):
            priority = "medium"
        conn = get_connection()
        conn.execute(
            "INSERT INTO assignments (title, subject, deadline, priority) VALUES (?,?,?,?)",
            (title, subject, deadline, priority),
        )
        conn.commit()
        conn.close()
        emoji = PRIORITY_EMOJI.get(priority, "⚪")
        return (f"✅ Assignment added: {emoji} **{title}** ({subject})\n"
                f"   Deadline: {deadline} | Priority: {priority.upper()}")
    except Exception as e:
        return f"❌ Error adding assignment: {e}"


@tool
def get_upcoming_assignments(days: int = 7) -> str:
    """Get all pending assignments due in the next N days (default 7)."""
    try:
        conn = get_connection()
        rows = conn.execute(
            """SELECT title, subject, deadline, priority FROM assignments
               WHERE deadline >= datetime('now', '+5.5 hours')
               AND deadline <= datetime('now', '+5.5 hours', ? || ' days')
               AND status = 'pending'
               ORDER BY deadline""",
            (str(days),),
        ).fetchall()
        conn.close()

        if not rows:
            return f"🎉 No pending assignments in the next {days} days. Keep it up!"

        lines = [f"📚 **Upcoming assignments (next {days} days):**"]
        for a in rows:
            emoji = PRIORITY_EMOJI.get(a["priority"], "⚪")
            lines.append(f"  {emoji} **{a['title']}** ({a['subject']}) — Due: {a['deadline']}")
        return "\n".join(lines)
    except Exception as e:
        return f"❌ Error fetching assignments: {e}"


@tool
def mark_assignment_done(title: str) -> str:
    """Mark an assignment as completed by its title (partial match ok)."""
    try:
        conn = get_connection()
        cursor = conn.execute(
            "UPDATE assignments SET status='done' WHERE title LIKE ? AND status='pending'",
            (f"%{title}%",),
        )
        conn.commit()
        count = cursor.rowcount
        conn.close()
        if count == 0:
            return f"⚠️ No pending assignment matching '{title}' found."
        return f"✅ Marked {count} assignment(s) matching '{title}' as done! 🎉"
    except Exception as e:
        return f"❌ Error: {e}"
