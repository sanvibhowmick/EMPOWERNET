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
    
    # 1. HIERARCHICAL LOCATION EXTRACTION
    # Recover District, Block, and Village from state (Previously captured)
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")

    # Guard: Ensure we have the minimum location data required for the tool
    if not district or not block or not village:
        return {
            "messages": [AIMessage(content="দয়া করে আপনার জেলা, ব্লক এবং গ্রামের নাম জানান যাতে আমি এই অভিযোগটি নথিভুক্ত করতে পারি।")],
            "next_agent": "supervisor"
        }

    # 2. TRANSLATION & CATEGORIZATION
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    translation_prompt = f"""
    Translate and summarize this worker's safety complaint into professional ENGLISH:
    User Message: "{last_msg}"
    
    Output format:
    Category: (Workplace, Infrastructure, or Health)
    English Description: (A clear 1-sentence summary in English)
    """
    
    ai_analysis = llm.invoke(translation_prompt).content
    
    category = "General Safety"
    english_desc = last_msg 
    
    lines = ai_analysis.strip().split("\n")
    for line in lines:
        if line.startswith("Category:"):
            category = line.replace("Category:", "").strip()
        if line.startswith("English Description:"):
            english_desc = line.replace("English Description:", "").strip()

    logger.info(f"🚩 Reporting Node: Processing {category} for {village}, {block}")

    # 3. TOOL INVOKE (No lat/lon passed here)
    # This matches the new tool schema we just created
    report_status = submit_safety_report.invoke({
        "user_id": str(user_id),
        "description": english_desc,
        "category": category,
        "district": district,
        "block": block,
        "village": village
    })

    # Return status report to the Writer for final Bengali response
    return {
        "messages": [AIMessage(content=f"SAFETY_REPORT_SUMMARY: {report_status}")],
        "next_agent": "writer"
    }