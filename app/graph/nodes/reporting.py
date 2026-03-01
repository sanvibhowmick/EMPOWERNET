import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.reporting import submit_safety_report

logger = logging.getLogger(__name__)

def reporting_node(state: AgentState):
    """
    The Reporting Specialist: Translates raw user complaints into 
    professional English safety reports and logs them.
    No hardcoded language strings.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""
    
    # 1. HIERARCHICAL LOCATION EXTRACTION
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")

    # Guard: If location is missing, we send a signal to the Writer to ask for it.
    # The Writer will handle the localized/language-aware response.
    if not district or not block or not village:
        return {
            "messages": [AIMessage(content="SIGNAL_ERROR:MISSING_LOCATION_FOR_REPORT")],
            "next_agent": "writer"
        }

    # 2. TRANSLATION & CATEGORIZATION (Internal Processing)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # We explicitly ask the LLM to handle the extraction logic 
    # so we don't have to hardcode "if line.startswith" loops
    translation_prompt = f"""
    Analyze this worker's safety complaint. 
    User Message: "{last_msg}"
    
    Return ONLY a valid JSON object with these keys:
    - category: (Workplace, Infrastructure, or Health)
    - description: (A clear 1-sentence summary in English)
    """
    
    try:
        ai_analysis = llm.invoke(translation_prompt).content
        # Basic cleanup in case the LLM adds markdown triple backticks
        import json
        clean_json = ai_analysis.strip().strip('`').replace('json', '')
        data = json.loads(clean_json)
        
        category = data.get("category", "General Safety")
        english_desc = data.get("description", last_msg)
    except Exception as e:
        logger.error(f"Failed to parse LLM analysis: {e}")
        category = "General Safety"
        english_desc = last_msg

    logger.info(f"🚩 Reporting Node: Processing {category} for {village}, {block}")

    # 3. TOOL INVOKE
    try:
        report_status = submit_safety_report.invoke({
            "user_id": str(user_id),
            "description": english_desc,
            "category": category,
            "district": district,
            "block": block,
            "village": village
        })
    except Exception as e:
        logger.error(f"Tool invocation failed: {e}")
        report_status = "Error submitting report."

    # Return a signal. The Writer node will pick this up and 
    # explain it nicely to the user in their preferred language.
    return {
        "messages": [AIMessage(content=f"SIGNAL_SUCCESS:SAFETY_REPORT_SUBMITTED|{report_status}")],
        "next_agent": "writer"
    }