import streamlit as st
import calendar
from database.db import get_connection
from datetime import datetime, date

TYPE_COLORS = {
    "class":  "#4A90E2",
    "exam":   "#E74C3C",
    "study":  "#27AE60",
    "lab":    "#9B59B6",
    "other":  "#F39C12",
}
TYPE_EMOJI = {
    "class": "📖", "exam": "📝", "study": "📚", "lab": "🔬", "other": "📌"
}

def render_calendar_view():
    st.subheader("📅 Monthly Schedule")

    # ── Add Event Quick-Form ──────────────────────────────────────────────────
    with st.expander("➕ Quick Add Event", expanded=False):
        with st.form("quick_add_event"):
            c1, c2 = st.columns(2)
            ev_title   = c1.text_input("Title", placeholder="e.g. Physics Lecture")
            ev_type    = c2.selectbox("Type", ["class", "exam", "study", "lab", "other"])
            c3, c4     = st.columns(2)
            ev_date    = c3.date_input("Date", value=date.today())
            ev_desc    = c4.text_input("Description (optional)")
            c5, c6     = st.columns(2)
            ev_start   = c5.time_input("Start Time")
            ev_end     = c6.time_input("End Time")
            submitted  = st.form_submit_button("Add Event")
            if submitted:
                if not ev_title.strip():
                    st.error("Please enter a title.")
                elif ev_start >= ev_end:
                    st.error("End time must be after start time.")
                else:
                    start_str = f"{ev_date} {ev_start.strftime('%H:%M')}"
                    end_str   = f"{ev_date} {ev_end.strftime('%H:%M')}"
                    try:
                        conn = get_connection()
                        conn.execute(
                            "INSERT INTO events (title, description, start_time, end_time, event_type) "
                            "VALUES (?,?,?,?,?)",
                            (ev_title.strip(), ev_desc.strip(), start_str, end_str, ev_type)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"✅ '{ev_title}' added for {start_str}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Could not save event: {e}")

    # ── Month Navigation ──────────────────────────────────────────────────────
    now = datetime.now()
    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = now.month
    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = now.year

    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        if st.button("◀ Prev"):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1
            st.rerun()
    with col2:
        m = st.session_state.calendar_month
        y = st.session_state.calendar_year
        st.markdown(
            f"<h3 style='text-align:center;margin:0'>{calendar.month_name[m]} {y}</h3>",
            unsafe_allow_html=True
        )
    with col3:
        if st.button("Next ▶"):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1
            st.rerun()

    # ── Fetch Events for This Month ───────────────────────────────────────────
    m = st.session_state.calendar_month
    y = st.session_state.calendar_year
    try:
        conn = get_connection()
        # Use column index fallback if event_type column missing (old DB)
        rows = conn.execute(
            "SELECT title, start_time, end_time, "
            "COALESCE(event_type, 'class') as event_type "
            "FROM events WHERE strftime('%Y-%m', start_time) = ?",
            (f"{y:04d}-{m:02d}",)
        ).fetchall()
        conn.close()
    except Exception:
        rows = []

    # Map day → list of (title, event_type)
    event_days: dict[int, list] = {}
    for r in rows:
        try:
            day = int(r["start_time"][8:10])
            event_days.setdefault(day, []).append((r["title"], r["event_type"] or "class"))
        except Exception:
            pass

    # ── Calendar Grid ─────────────────────────────────────────────────────────
    today_day = now.day if (now.month == m and now.year == y) else -1

    st.markdown("""
    <style>
    .cal-header { text-align:center; font-weight:700; padding:6px 0;
                  color:#888; font-size:13px; text-transform:uppercase; }
    .cal-cell   { border:1px solid #2a2a2a; border-radius:8px; padding:6px;
                  min-height:64px; font-size:13px; }
    .cal-today  { border:2px solid #4A90E2 !important; background:#0a1f3c !important; }
    .cal-dot    { display:inline-block; width:8px; height:8px; border-radius:50%;
                  margin:1px; }
    </style>""", unsafe_allow_html=True)

    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    header_cols = st.columns(7)
    for i, d in enumerate(day_names):
        header_cols[i].markdown(
            f"<div class='cal-header'>{d}</div>", unsafe_allow_html=True
        )

    for week in calendar.monthcalendar(y, m):
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            with week_cols[i]:
                if day == 0:
                    st.markdown("<div class='cal-cell'></div>", unsafe_allow_html=True)
                    continue
                is_today = (day == today_day)
                today_cls = "cal-today" if is_today else ""
                today_label = " 🔵" if is_today else ""
                events_html = ""
                for (title, etype) in event_days.get(day, []):
                    color = TYPE_COLORS.get(etype, "#F39C12")
                    emoji = TYPE_EMOJI.get(etype, "📌")
                    events_html += (
                        f"<div style='font-size:11px;margin-top:2px;"
                        f"color:{color};white-space:nowrap;overflow:hidden;"
                        f"text-overflow:ellipsis' title='{title}'>"
                        f"{emoji} {title}</div>"
                    )
                st.markdown(
                    f"<div class='cal-cell {today_cls}'>"
                    f"<b>{day}{today_label}</b>"
                    f"{events_html}</div>",
                    unsafe_allow_html=True
                )

    # ── Legend ────────────────────────────────────────────────────────────────
    st.markdown("---")
    leg_cols = st.columns(len(TYPE_COLORS))
    for i, (etype, color) in enumerate(TYPE_COLORS.items()):
        leg_cols[i].markdown(
            f"<span style='color:{color}'>●</span> {TYPE_EMOJI[etype]} {etype.capitalize()}",
            unsafe_allow_html=True
        )

    # ── Selected Month Events List ────────────────────────────────────────────
    if rows:
        st.markdown(f"### All events in {calendar.month_name[m]}")
        for r in rows:
            etype = r["event_type"] or "class"
            color = TYPE_COLORS.get(etype, "#F39C12")
            emoji = TYPE_EMOJI.get(etype, "📌")
            st.markdown(
                f"<div style='padding:8px 12px;margin:4px 0;border-left:4px solid {color};"
                f"background:#1a1a1a;border-radius:4px'>"
                f"{emoji} <b>{r['title']}</b> &nbsp;&nbsp; "
                f"<span style='color:#888'>{r['start_time']} → {r['end_time'][11:16]}</span>"
                f"</div>",
                unsafe_allow_html=True
            )
