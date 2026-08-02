# app/graph/nodes/reporting.py

import logging
from typing import Literal, Optional
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState
from app.tools.reporting import submit_safety_report
from app.tools.spatial import get_village_coordinates

logger = logging.getLogger(__name__)



class SafetyReportExtraction(BaseModel):
    """Structured extraction of a worker's safety complaint."""
    category: Literal["Workplace", "Infrastructure", "Health"] = Field(
        description="The type of safety issue being reported."
    )
    description: str = Field(
        description="A clear, one-sentence summary of the complaint, in English."
    )


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
            "next_agent": "writer",
            "specialist_done": True,
        }

    # 2. TRANSLATION & CATEGORIZATION (Internal Processing) -- now via
    # structured output instead of manual JSON string parsing.
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    structured_llm = llm.with_structured_output(SafetyReportExtraction)

    try:
        extracted = structured_llm.invoke(
            f"Analyze this worker's safety complaint and classify it.\n"
            f'User Message: "{last_msg}"'
        )
        category = extracted.category
        english_desc = extracted.description
    except Exception as e:
        logger.error(f"Failed to extract structured report: {e}")
        category = "General Safety"
        english_desc = last_msg

    logger.info(f"🚩 Reporting Node: Processing {category} for {village}, {block}")


    lat: Optional[float] = None
    lon: Optional[float] = None
    try:
        coords = get_village_coordinates.invoke({"district": district, "block": block, "village": village})
        if coords:
            lat, lon = coords
    except Exception as e:
        logger.warning(f"Could not resolve coordinates for {village}, {block}: {e}")

    # 3. TOOL INVOKE
    try:
        report_status = submit_safety_report.invoke({
            "user_id": str(user_id),
            "description": english_desc,
            "category": category,
            "district": district,
            "block": block,
            "village": village,
            "lat": lat,
            "lon": lon,
        })
    except Exception as e:
        logger.error(f"Tool invocation failed: {e}")
        report_status = "Error submitting report."

    # Return a signal. The Writer node will pick this up and
    # explain it nicely to the user in their preferred language.
    return {
        "messages": [AIMessage(content=f"SIGNAL_SUCCESS:SAFETY_REPORT_SUBMITTED|{report_status}")],
        "next_agent": "writer",
        "specialist_done": True,
    }
