# Smart Timetable Assistant 📅🤖

A conversational, agentic scheduling assistant built with **Streamlit**, **LangChain**, and **SQLite**, featuring dynamic **Google Calendar Synchronization**, **Conflict Detection**, and a **Glassmorphic UI**.

---

## Features

1. **🤖 Conversational AI Agent**: Driven by Google Gemini or OpenAI. Simply chat with the assistant to schedule, update, reschedule, or cancel events using natural language.
2. **📅 Custom Glassmorphic Calendar**: CSS Grid-based layout presenting daily and weekly timetables with status indicators, color-coded categories, and duration details.
3. **🔒 Local SQLite Storage & Sync**: A robust local SQLite database that maintains complete timetable details, functioning fully offline.
4. **🔌 Google Calendar Sync**: Automatically creates, updates, and deletes events from your Google Calendar account when connected. Falls back gracefully to offline mode if configuration is missing.
5. **⚠️ Conflict Detection & Free-Slot Proposing**: The assistant automatically scans for overlaps. If a conflict occurs, it uses conflict-resolution tools to locate next available free slots during working hours (9 AM - 6 PM) and presents them to you.
6. **🔔 Live Notifications**: Proactively polls the database to identify events starting in the next 30 minutes, delivering instant notification toasts directly in the UI.

---

## Setup Instructions

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

### 2. Install Dependencies
Navigate to the directory and install python packages:
```bash
cd smart-timetable-assistant
pip install -r requirements.txt
```

### 3. API Keys Configuration
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_google_gemini_api_key
# OR
OPENAI_API_KEY=your_openai_api_key
```
Alternatively, you can input your API key directly inside the app's sidebar interface.

### 4. Enable Google Calendar API (Optional)
To synchronize events with Google Calendar:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Google Calendar API**.
3. Configure the OAuth Consent Screen and create **OAuth 2.0 Client IDs** (Application Type: **Desktop Application**).
4. Download the JSON credentials file and rename it to `credentials.json`.
5. Place `credentials.json` in the root of the `smart-timetable-assistant` folder.
6. Upon running the app and clicking "Sync Google Calendar", your browser will prompt you to authenticate. Subsequent launches will use the cached `token.json` automatically.

---

## Run the Application

Start the Streamlit server:
```bash
streamlit run app.py
```
This will open the application in your browser (usually at `http://localhost:8501`).

---

## Folder Architecture

```
smart-timetable-assistant/
├── .env
├── .gitignore
├── requirements.txt
├── README.md
├── app.py                     # Main Streamlit entry point & layouts
├── agent/                     # LangChain Agent setup and prompts
├── tools/                     # Calendar CRUD, Conflict suggestions, Reminders
├── database/                  # SQLite connection and helper queries
├── ui/                        # Styled Streamlit components
└── utils/                     # Google Auth & general date helpers
```
