from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from app.tools.reporting import submit_safety_report
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def chaukas_node(state: AgentState, config: RunnableConfig):
    """
    The Chaukas (Watchful) node.
    Analyzes safety complaints and updates the reporting database with token enforcement.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = next((m.content for m in reversed(messages) if m.type == "human"), "")

    # 1. AI Severity Analysis (Financial Shield Applied)
    # HARD CAP: max_tokens=20 ensures it only returns the number score
    llm_analysis = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=20)
    
    analysis_prompt = (
        "Analyze the following complaint for distress level and danger. "
        "Return a severity score between 0.0 (low concern) and 1.0 (immediate danger). "
        "Return ONLY the number.\n\n"
        f"Complaint: {last_msg}"
    )
    
    try:
        severity = float(llm_analysis.invoke(analysis_prompt).content.strip())
    except:
        severity = 0.5  # Fallback

    # 2. Dynamic Location Retrieval
    profile = get_user_context.invoke({"phone_number": user_id})
    user_lat, user_lon = profile.get("lat"), profile.get("lon")

    print(f"👁️ Chaukas: Logging report for {user_id} with severity {severity}")

    # 3. Call the Reporting Tool
    report_status = submit_safety_report.invoke({
        "user_id": user_id,
        "description": last_msg,
        "lat": user_lat,
        "lon": user_lon,
        "severity": severity
    })

    # 4. Response Logic (Global Limit Enforcement)
    # Reads 'max_tokens' (400) from your main.py config
    limit = config.get("configurable", {}).get("max_tokens", 400)
    
    if severity > 0.8:
        response = f"{report_status} This sounds very serious. I am notifying the 'Durga' emergency node now."
    else:
        response = f"{report_status} Thank you for reporting this. By speaking up, you are making the community safer for everyone."

    return {
        "messages": [AIMessage(content=response)],
        "next_agent": "supervisor"
    }