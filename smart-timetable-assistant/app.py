import streamlit as st
from database.db import init_db, get_connection
from agent.timetable_agent import create_timetable_agent
from ui.dashboard import render_dashboard
from ui.calendar_view import render_calendar_view
from ui.chat_interface import render_chat_interface
import sys
import os

# Windows console UTF-8 fix
if sys.platform == "win32" and not getattr(sys.stdout, "_is_utf8_wrapped", False):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    sys.stdout._is_utf8_wrapped = True
    sys.stderr._is_utf8_wrapped = True

st.set_page_config(
    page_title="Smart Timetable Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Dark base */
[data-testid="stAppViewContainer"] { background: #0f0f0f; }
[data-testid="stSidebar"]           { background: #141414; border-right: 1px solid #222; }
/* Sidebar title */
.sidebar-title {
    font-size: 22px; font-weight: 700; color: #4A90E2;
    margin-bottom: 4px; letter-spacing: -0.5px;
}
/* Metric cards */
[data-testid="metric-container"] {
    background: #1a1a1a; border: 1px solid #2a2a2a;
    border-radius: 10px; padding: 12px 16px;
}
/* Chat bubbles */
[data-testid="stChatMessage"] { border-radius: 12px; }
/* Buttons */
.stButton > button {
    border-radius: 8px; font-size: 13px;
    transition: all .15s ease;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px #0004; }
/* Expander */
[data-testid="stExpander"] { border: 1px solid #2a2a2a !important; border-radius: 8px; }
/* Input */
[data-testid="stChatInput"] textarea { background: #1a1a1a !important; }
</style>
""", unsafe_allow_html=True)

# ── Init DB ──────────────────────────────────────────────────────────────────
init_db()

# ── Load Agent (cached) ──────────────────────────────────────────────────────
@st.cache_resource(show_spinner="🤖 Loading AI model…")
def load_agent():
    try:
        return create_timetable_agent()
    except Exception as e:
        return None

agent = load_agent()

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='sidebar-title'>🎓 Timetable AI</div>", unsafe_allow_html=True)
    st.caption("Smart scheduling for Indian students")
    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["💬 Chat", "📊 Dashboard", "📅 Calendar"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("**📊 Quick Stats**")
    try:
        conn = get_connection()
        from datetime import date
        today = date.today().isoformat()
        event_count      = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        today_count      = conn.execute(
            "SELECT COUNT(*) FROM events WHERE start_time LIKE ?", (f"{today}%",)
        ).fetchone()[0]
        pending_count    = conn.execute(
            "SELECT COUNT(*) FROM assignments WHERE status='pending'"
        ).fetchone()[0]
        conn.close()
        col1, col2 = st.columns(2)
        col1.metric("Events", event_count)
        col2.metric("Today",  today_count)
        st.metric("Pending Tasks", pending_count)
    except Exception:
        st.caption("Stats unavailable")

    st.markdown("---")

    # AI status badge
    if agent:
        st.success("🤖 AI Ready")
    else:
        st.error("⚠️ AI unavailable — check your API key in .env")

    st.markdown("---")
    st.caption("Made for Indian College Students 🇮🇳")

# ── Main Content ─────────────────────────────────────────────────────────────
if page == "💬 Chat":
    if agent is None:
        st.error(
            "⚠️ **AI Agent could not be loaded.**\n\n"
            "Please check that your Gemini API key is correctly set in the `.env` file:\n"
            "```\nOPENAI_API_KEY=your_gemini_key_here\n```"
        )
    else:
        render_chat_interface(agent)

elif page == "📊 Dashboard":
    render_dashboard()

elif page == "📅 Calendar":
    render_calendar_view()
