import streamlit as st
from database.db import get_connection
from datetime import datetime, date, timedelta
import pytz

PRIORITY_STYLE = {
    "high":   ("🔴", "#E74C3C"),
    "medium": ("🟡", "#F39C12"),
    "low":    ("🟢", "#27AE60"),
}

def _ist_now():
    return datetime.now(pytz.timezone("Asia/Kolkata"))

def render_dashboard():
    now = _ist_now()
    today = now.strftime("%Y-%m-%d")

    st.markdown(f"""
    <div style='padding:12px 0 4px;'>
        <h2 style='margin:0'>👋 Good {'Morning' if now.hour < 12 else 'Afternoon' if now.hour < 17 else 'Evening'}!</h2>
        <p style='color:#888;margin:4px 0 0'>{now.strftime('%A, %d %B %Y')} &nbsp;|&nbsp; {now.strftime('%I:%M %p')} IST</p>
    </div>
    """, unsafe_allow_html=True)

    # ── Metric row ────────────────────────────────────────────────────────────
    try:
        conn = get_connection()
        total_events     = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        today_count      = conn.execute(
            "SELECT COUNT(*) FROM events WHERE start_time LIKE ?", (f"{today}%",)
        ).fetchone()[0]
        pending_count    = conn.execute(
            "SELECT COUNT(*) FROM assignments WHERE status='pending'"
        ).fetchone()[0]
        overdue_count    = conn.execute(
            "SELECT COUNT(*) FROM assignments WHERE status='pending' "
            "AND deadline < datetime('now', '+5.5 hours')"
        ).fetchone()[0]
        conn.close()
    except Exception:
        total_events = today_count = pending_count = overdue_count = 0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📚 Total Events",     total_events)
    m2.metric("🗓️ Today's Classes",  today_count)
    m3.metric("📝 Pending Tasks",    pending_count, delta=f"-{overdue_count} overdue" if overdue_count else None, delta_color="inverse")
    m4.metric("⏰ Overdue",          overdue_count)

    st.markdown("---")

    col1, col2 = st.columns(2)

    # ── Today's Events ────────────────────────────────────────────────────────
    with col1:
        st.markdown("### 🗓️ Today's Schedule")
        try:
            conn = get_connection()
            events = conn.execute(
                "SELECT title, start_time, end_time, "
                "COALESCE(event_type,'class') as event_type "
                "FROM events WHERE start_time LIKE ? ORDER BY start_time",
                (f"{today}%",),
            ).fetchall()
            conn.close()
        except Exception:
            events = []

        TYPE_COLORS = {"class":"#4A90E2","exam":"#E74C3C","study":"#27AE60","lab":"#9B59B6","other":"#F39C12"}
        if events:
            for e in events:
                color = TYPE_COLORS.get(e["event_type"], "#F39C12")
                start = e["start_time"][11:16]
                end   = e["end_time"][11:16]
                # Highlight currently-ongoing event
                try:
                    s_dt = datetime.strptime(e["start_time"], "%Y-%m-%d %H:%M")
                    e_dt = datetime.strptime(e["end_time"],   "%Y-%m-%d %H:%M")
                    is_now = s_dt.hour <= now.hour <= e_dt.hour
                except Exception:
                    is_now = False
                badge = " 🔴 LIVE" if is_now else ""
                st.markdown(
                    f"<div style='padding:10px 14px;margin:6px 0;"
                    f"border-left:4px solid {color};background:#1a1a1a;border-radius:6px'>"
                    f"<b>{e['title']}</b>{badge}<br>"
                    f"<span style='color:#888;font-size:13px'>{start} – {end}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.success("No classes today! Great time to study or rest. 🎉")

        # Quick add via form
        with st.expander("➕ Add today's event"):
            with st.form("add_today"):
                t  = st.text_input("Title")
                et = st.selectbox("Type", ["class","exam","study","lab","other"])
                c1, c2 = st.columns(2)
                ts = c1.time_input("Start")
                te = c2.time_input("End")
                if st.form_submit_button("Add"):
                    if t.strip() and ts < te:
                        start_str = f"{today} {ts.strftime('%H:%M')}"
                        end_str   = f"{today} {te.strftime('%H:%M')}"
                        conn = get_connection()
                        conn.execute(
                            "INSERT INTO events (title, start_time, end_time, event_type) VALUES (?,?,?,?)",
                            (t.strip(), start_str, end_str, et)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Added: {t}")
                        st.rerun()
                    else:
                        st.error("Please enter a valid title and ensure end > start.")

    # ── Upcoming Assignments ──────────────────────────────────────────────────
    with col2:
        st.markdown("### 📝 Assignments & Deadlines")
        try:
            conn = get_connection()
            assignments = conn.execute(
                """SELECT title, subject, deadline, priority, status
                   FROM assignments
                   WHERE status = 'pending'
                   ORDER BY deadline
                   LIMIT 10"""
            ).fetchall()
            conn.close()
        except Exception:
            assignments = []

        if assignments:
            for a in assignments:
                emoji, color = PRIORITY_STYLE.get(a["priority"], ("⚪", "#888"))
                try:
                    dl = datetime.strptime(a["deadline"], "%Y-%m-%d %H:%M")
                    diff = dl - now.replace(tzinfo=None)
                    days_left = diff.days
                    if days_left < 0:
                        urgency = "🚨 OVERDUE"
                        bg = "#2d0a0a"
                    elif days_left == 0:
                        urgency = "⚡ DUE TODAY"
                        bg = "#1e1a00"
                    elif days_left == 1:
                        urgency = "⏳ Tomorrow"
                        bg = "#1a1200"
                    else:
                        urgency = f"📅 {days_left}d left"
                        bg = "#1a1a1a"
                except Exception:
                    urgency, bg = "", "#1a1a1a"

                st.markdown(
                    f"<div style='padding:10px 14px;margin:6px 0;"
                    f"border-left:4px solid {color};background:{bg};border-radius:6px'>"
                    f"{emoji} <b>{a['title']}</b> <span style='color:#888;font-size:12px'>({a['subject']})</span><br>"
                    f"<span style='color:#888;font-size:12px'>{a['deadline']} &nbsp;|&nbsp; {urgency}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.success("No pending assignments! You're all caught up. 🎉")

        # Quick add assignment
        with st.expander("➕ Add assignment"):
            with st.form("add_assignment"):
                at  = st.text_input("Title")
                sub = st.text_input("Subject")
                c1, c2 = st.columns(2)
                dl  = c1.date_input("Deadline date")
                tm  = c2.time_input("Deadline time")
                pri = st.select_slider("Priority", ["low","medium","high"], value="medium")
                if st.form_submit_button("Add"):
                    if at.strip() and sub.strip():
                        deadline_str = f"{dl} {tm.strftime('%H:%M')}"
                        conn = get_connection()
                        conn.execute(
                            "INSERT INTO assignments (title, subject, deadline, priority) VALUES (?,?,?,?)",
                            (at.strip(), sub.strip(), deadline_str, pri)
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"Added: {at}")
                        st.rerun()
                    else:
                        st.error("Fill in title and subject.")

    # ── This Week Overview ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📆 This Week's Schedule")
    week_start = now.date() - timedelta(days=now.weekday())
    week_days = [week_start + timedelta(days=i) for i in range(7)]
    day_cols = st.columns(7)
    for i, d in enumerate(week_days):
        with day_cols[i]:
            label = d.strftime("%a\n%d")
            is_today_col = (d == now.date())
            st.markdown(
                f"<div style='text-align:center;font-weight:{'700' if is_today_col else '400'};"
                f"color:{'#4A90E2' if is_today_col else '#ccc'};font-size:13px'>"
                f"{label.replace(chr(10), '<br>')}</div>",
                unsafe_allow_html=True
            )
            try:
                conn = get_connection()
                day_events = conn.execute(
                    "SELECT title, COALESCE(event_type,'class') as event_type "
                    "FROM events WHERE start_time LIKE ? ORDER BY start_time",
                    (f"{d.isoformat()}%",),
                ).fetchall()
                conn.close()
            except Exception:
                day_events = []
            TYPE_COLORS = {"class":"#4A90E2","exam":"#E74C3C","study":"#27AE60","lab":"#9B59B6","other":"#F39C12"}
            for ev in day_events[:3]:
                c = TYPE_COLORS.get(ev["event_type"], "#F39C12")
                ev_title = ev["title"]
                st.markdown(
                    f"<div style='background:{c}22;border-left:3px solid {c};"
                    f"border-radius:4px;padding:2px 6px;margin:2px 0;"
                    f"font-size:11px;overflow:hidden;text-overflow:ellipsis;"
                    f"white-space:nowrap' title='{ev_title}'>{ev_title}</div>",
                    unsafe_allow_html=True
                )
            if len(day_events) > 3:
                st.caption(f"+{len(day_events)-3} more")
