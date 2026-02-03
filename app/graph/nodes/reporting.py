import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.reporting import submit_safety_report

logger = logging.getLogger(__name__)

def reporting_node(state: AgentState):
    """
    The Reporting Specialist: Translates raw user complaints into 
    English safety reports and logs them in the database.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""
    
    lat = state.get("lat")
    lon = state.get("lon")

    # 1. COORDINATE GUARD
    if lat is None or lon is None:
        return {
            "messages": [AIMessage(content="SAFETY_REPORT_ERROR: I need your location to log this issue.")],
            "next_agent": "supervisor"
        }

    # 2. TRANSLATION & CATEGORIZATION (AI GATEWAY)
    # We force the LLM to provide a clean English translation of the complaint
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    translation_prompt = f"""
    Translate and summarize this worker's safety complaint into professional ENGLISH:
    User Message: "{last_msg}"
    
    Output format:
    Category: (Workplace, Infrastructure, or Health)
    English Description: (A clear 1-sentence summary in English)
    """
    
    ai_analysis = llm.invoke(translation_prompt).content
    
    # Extracting the category and English text from the AI response
    # (Simple parsing logic)
    category = "General Safety"
    english_desc = last_msg # Fallback
    
    if "Category:" in ai_analysis:
        parts = ai_analysis.split("\n")
        category = parts[0].replace("Category:", "").strip()
        english_desc = parts[1].replace("English Description:", "").strip()

    logger.info(f"🚩 Translated Report for DB: {english_desc} ({category})")

    # 3. SUBMIT TO DB (Using the English Description)
    report_status = submit_safety_report.invoke({
        "user_id": str(user_id),
        "description": english_desc, # English version stored
        "category": category,
        "lat": float(lat),
        "lon": float(lon)
    })

    return {
        "messages": [AIMessage(content=f"SAFETY_REPORT_SUMMARY: {report_status}")],
        "next_agent": "writer"
    }