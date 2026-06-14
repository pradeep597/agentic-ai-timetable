import streamlit as st
from agent.timetable_agent import invoke_agent

EXAMPLES = [
    ("📖 Schedule class",     "Schedule Physics lecture tomorrow 10am to 11:30am"),
    ("🔍 Find free slot",     "Find me a free 2-hour slot this Friday"),
    ("📝 Add assignment",     "Add assignment: Math homework due 2026-06-20 23:59, high priority, subject Math"),
    ("📅 Today's events",    "What events do I have today?"),
    ("⏰ Upcoming deadlines", "Show my upcoming assignments this week"),
    ("✅ Mark done",          "Mark Math homework as done"),
]

def render_chat_interface(agent):
    st.subheader("💬 Timetable AI — Chat")

    if "messages" not in st.session_state:
        st.session_state.messages = []
        # Friendly first message
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "👋 Hi! I'm your **Smart Timetable Assistant**.\n\n"
                "I can help you:\n"
                "- 📖 Schedule classes, exams, study sessions\n"
                "- 📝 Track assignments and deadlines\n"
                "- 🔍 Find free time slots\n"
                "- ⚠️ Detect scheduling conflicts\n\n"
                "Just type what you need, or click a quick prompt below!"
            )
        })

    # ── Render chat history ───────────────────────────────────────────────────
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ── Quick prompt chips ────────────────────────────────────────────────────
    st.markdown("**Quick prompts:**")
    chip_cols = st.columns(3)
    for i, (label, prompt) in enumerate(EXAMPLES):
        if chip_cols[i % 3].button(label, key=f"chip_{i}", use_container_width=True):
            st.session_state.pending_input = prompt
            st.rerun()

    # ── Chat input ────────────────────────────────────────────────────────────
    user_input = st.chat_input("Ask about your schedule, deadlines, free slots…")

    if "pending_input" in st.session_state:
        user_input = st.session_state.pop("pending_input")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                answer = invoke_agent(agent, user_input)
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

    # ── Clear chat button ─────────────────────────────────────────────────────
    if len(st.session_state.messages) > 1:
        if st.button("🗑️ Clear chat", key="clear_chat"):
            st.session_state.messages = []
            st.rerun()
