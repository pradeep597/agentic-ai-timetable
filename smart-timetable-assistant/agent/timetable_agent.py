from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferWindowMemory
from tools.calendar_tool import create_event, get_events, find_free_slots
from tools.conflict_tool import check_conflict, add_assignment, get_upcoming_assignments, mark_assignment_done
from dotenv import load_dotenv
import os

load_dotenv()

def _resolve_gemini_key() -> str | None:
    """Return the Gemini/Google API key from any env variable the user may have set."""
    for var in ("GOOGLE_API_KEY", "GEMINI_API_KEY", "OPENAI_API_KEY"):
        val = os.getenv(var, "").strip()
        if val and val not in ("your_openai_key_here", "your_google_key_here", "fff", ""):
            # Accept any key that is NOT an OpenAI sk- key
            if not val.startswith("sk-"):
                return val
    return None


def _auto_select_gemini_model(api_key: str) -> str:
    """Try models in preference order; return first that works."""
    preferred = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-pro",
        "gemini-flash-latest",
    ]
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        available = {m.name.replace("models/", "") for m in genai.list_models()}
        for model in preferred:
            if model in available:
                return model
        # Fallback: return first text model
        for m in preferred:
            return m
    except Exception:
        pass
    return "gemini-2.5-flash"


def create_timetable_agent():
    from agent.prompts import get_system_prompt  # fresh each call → live timestamp

    tools = [
        create_event,
        get_events,
        find_free_slots,
        check_conflict,
        add_assignment,
        get_upcoming_assignments,
        mark_assignment_done,
    ]

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}"),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    memory = ConversationBufferWindowMemory(
        memory_key="chat_history",
        return_messages=True,
        k=15
    )

    google_key = _resolve_gemini_key()

    if google_key:
        os.environ["GOOGLE_API_KEY"] = google_key
        from langchain_google_genai import ChatGoogleGenerativeAI
        model_name = _auto_select_gemini_model(google_key)
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0.2,
            convert_system_message_to_human=True,
        )
        print(f"[Agent] Using Gemini model: {model_name}")
    else:
        from langchain_openai import ChatOpenAI
        from langchain.agents import create_openai_functions_agent
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        agent = create_openai_functions_agent(llm, tools, prompt)
        return AgentExecutor(
            agent=agent, tools=tools, memory=memory,
            verbose=False, handle_parsing_errors=True, max_iterations=6,
        )

    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent, tools=tools, memory=memory,
        verbose=False, handle_parsing_errors=True, max_iterations=6,
    )


def invoke_agent(agent, user_input: str) -> str:
    """Safe wrapper around agent.invoke — always returns a string."""
    from agent.prompts import get_system_prompt
    try:
        result = agent.invoke({
            "input": user_input,
            "system_prompt": get_system_prompt(),
        })
        return result.get("output", "I couldn't process that request.")
    except Exception as e:
        err = str(e)
        if "credentials.json" in err:
            return ("⚠️ Google Calendar is not connected. Your event has been saved locally.\n\n"
                    "To enable Google sync, add `credentials.json` to the project folder.")
        if "404" in err and "not found" in err:
            return ("⚠️ The AI model returned an error. Please refresh the page — "
                    "the app will automatically pick a working Gemini model.")
        return f"⚠️ Something went wrong: {err}"
