from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.tools.reporting import submit_safety_report
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def chaukas_node(state: AgentState):
    """
    The Chaukas (Watchful) node.
    Analyzes safety complaints and updates the reporting database.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = next((m.content for m in reversed(messages) if m.type == "human"), "")

    # 1. AI Stress & Severity Analysis
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    analysis_prompt = (
        "Analyze the following complaint for distress level and danger. "
        "Return a severity score between 0.0 (low concern) and 1.0 (immediate danger). "
        "Return ONLY the number.\n\n"
        f"Complaint: {last_msg}"
    )
    
    try:
        severity = float(llm.invoke(analysis_prompt).content.strip())
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

    # 4. Response Logic
    if severity > 0.8:
        response = f"{report_status} This sounds very serious. I am notifying the 'Durga' emergency node now."
    else:
        response = f"{report_status} Thank you for reporting this. By speaking up, you are making the community safer for everyone."

    return {
        "messages": [AIMessage(content=response)],
        "next_agent": "supervisor"
    }