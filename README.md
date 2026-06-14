Smart Timetable Assistant 📅🤖
A conversational, agentic scheduling assistant built with Streamlit, LangChain, and SQLite, featuring dynamic Google Calendar Synchronization, Conflict Detection, and a Glassmorphic UI.

Features
🤖 Conversational AI Agent: Driven by Google Gemini or OpenAI. Simply chat with the assistant to schedule, update, reschedule, or cancel events using natural language.
📅 Custom Glassmorphic Calendar: CSS Grid-based layout presenting daily and weekly timetables with status indicators, color-coded categories, and duration details.
🔒 Local SQLite Storage & Sync: A robust local SQLite database that maintains complete timetable details, functioning fully offline.
🔌 Google Calendar Sync: Automatically creates, updates, and deletes events from your Google Calendar account when connected. Falls back gracefully to offline mode if configuration is missing.
⚠️ Conflict Detection & Free-Slot Proposing: The assistant automatically scans for overlaps. If a conflict occurs, it uses conflict-resolution tools to locate next available free slots during working hours (9 AM - 6 PM) and presents them to you.
🔔 Live Notifications: Proactively polls the database to identify events starting in the next 30 minutes, delivering instant notification toasts directly in the UI.
