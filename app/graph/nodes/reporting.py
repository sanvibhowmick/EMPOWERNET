import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.reporting import submit_safety_report

logger = logging.getLogger(__name__)

def reporting_node(state: AgentState):
    """
    The Reporting Specialist: Translates raw user complaints into 
    professional English safety reports and logs them using 
    the Village/Block hierarchy.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""
    
    # 1. HIERARCHICAL LOCATION GUARD
    # Recover District, Block, and Village from state
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")

    # If the user's location hierarchy is unknown, we cannot log the report
    if not district or not block or not village:
        return {
            "messages": [AIMessage(content="SAFETY_REPORT_ERROR: I need to know your district, block, and village to log this issue accurately.")],
            "next_agent": "supervisor"
        }

    # 2. TRANSLATION & CATEGORIZATION (AI GATEWAY)
    # We force the LLM to provide a clean English translation for our NGO partners
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    translation_prompt = f"""
    Translate and summarize this worker's safety complaint into professional ENGLISH:
    User Message: "{last_msg}"
    
    Output format:
    Category: (Workplace, Infrastructure, or Health)
    English Description: (A clear 1-sentence summary in English)
    """
    
    ai_analysis = llm.invoke(translation_prompt).content
    
    # Simple extraction logic from the AI response
    category = "General Safety"
    english_desc = last_msg # Fallback if parsing fails
    
    lines = ai_analysis.strip().split("\n")
    for line in lines:
        if line.startswith("Category:"):
            category = line.replace("Category:", "").strip()
        if line.startswith("English Description:"):
            english_desc = line.replace("English Description:", "").strip()

    logger.info(f"🚩 Translated Report for DB: {english_desc} ({category}) at {village}, {block}")

    # 3. SUBMIT TO DB (Using Hierarchical Fields)
    # This tool call will automatically penalize (score -0.5) all vetted job sites
    # in the reporter's specific village and block.
    report_status = submit_safety_report.invoke({
        "user_id": str(user_id),
        "description": english_desc,
        "category": category,
        "district": district,
        "block": block,
        "village": village
    })

    # Return status report to be handled by the Writer (for translation back to native lang)
    return {
        "messages": [AIMessage(content=f"SAFETY_REPORT_SUMMARY: {report_status}")],
        "next_agent": "writer"
    }