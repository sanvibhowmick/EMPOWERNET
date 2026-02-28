# app/graph/nodes/supervisor.py

import logging
from typing import Literal
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

# 1. Define the Router Schema
class RouterResponse(BaseModel):
    """Decides which specialist agent should handle the turn."""
    next_agent: Literal["legal", "reporting", "opportunity", "writer", "end"] = Field(
        description="The name of the next specialist or 'writer' to respond."
    )
    reasoning: str = Field(description="Internal logic for choosing this path.")

def supervisor_node(state: AgentState):
    """
    The Brain: Analyzes user intent and specialist findings.
    Now includes a Location Guard for hierarchical onboarding.
    """
    
    # --- HARD GUARD 1: BREAK THE LOOP ---
    # If a specialist has finished, always go to the writer
    last_msg = state["messages"][-1].content if state["messages"] else ""
    if any(keyword in last_msg for keyword in ["SUMMARY", "REPORT", "FINDINGS"]):
        logger.info(f"✅ Specialist work complete. Routing to WRITER.")
        return {"next_agent": "writer"}
    
    # --- HARD GUARD 2: LOCATION ONBOARDING ---
    # We cannot provide location-based jobs or legal zone data without a village
    district = state.get("district")
    block = state.get("block")
    village = state.get("village")

    # If the user is trying to find work/laws but we don't know their location
    # we route to 'writer' with instructions to ask for location.
    if not (district and block and village):
        # Allow simple greetings to pass, but intercept search/report intents
        intent_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        is_action_request = intent_llm.invoke(
            f"Is the user asking for a job, legal help, or reporting an issue? Message: '{last_msg}'. Reply YES or NO."
        ).content.strip().upper()

        if "YES" in is_action_request:
            logger.info("📍 Location missing for action request. Routing to WRITER for onboarding.")
            return {"next_agent": "writer"}
    # -----------------------------------------

    # Initialize structured LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(RouterResponse)

    # 2. System Prompt defining the Swarm's logic
    system_prompt = (
        "You are the Supervisor for EmpowerNet, an assistant for rural workers in West Bengal.\n\n"
        "YOUR ROUTING RULES:\n"
        "1. LEGAL: Use if the user asks about wages, rights, or laws. Needs 'district' for Zone logic.\n"
        "2. REPORTING: Use for NEW safety complaints. Needs 'village' to penalize sites.\n"
        "3. OPPORTUNITY: Use for finding jobs, training, or SHGs. Needs 'village' for local matching.\n"
        "4. WRITER: Use for greetings, location onboarding (if location is missing), or finishing reports.\n"
        "5. END: Only use if the user says goodbye.\n\n"
        f"CURRENT USER LOCATION: District: {district}, Block: {block}, Village: {village}\n"
        "If location is missing and user wants jobs/laws, route to WRITER to ask for their District."
    )

    # 3. Call the Decision Maker
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    decision = structured_llm.invoke(messages)
    
    logger.info(f"🧠 Supervisor Path: {decision.next_agent} | {decision.reasoning}")

    return {
        "next_agent": decision.next_agent
    }