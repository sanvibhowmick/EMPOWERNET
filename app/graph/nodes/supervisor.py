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
    The Brain: Analyzes user intent and specialist findings to route the state.
    """
    # --- HARD GUARD: BREAK THE LOOP ---
    # Check the very last message. If it's a summary from a specialist, 
    # we MUST go to the writer. No LLM needed.
    last_msg = state["messages"][-1].content if state["messages"] else ""
    
    if any(keyword in last_msg for keyword in ["SUMMARY", "REPORT", "FINDINGS"]):
        logger.info(f"✅ Specialist work complete. Bypassing LLM to route to WRITER.")
        return {"next_agent": "writer"}
    # ----------------------------------

    # Initialize structured LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(RouterResponse)

    # 2. System Prompt defining the Swarm's logic
    system_prompt = (
        "You are the Supervisor for EmpowerNet, an assistant for rural women workers.\n\n"
        "YOUR ROUTING RULES:\n"
        "1. LEGAL: Use if the user asks about wages, rights, or laws.\n"
        "2. REPORTING: Use for NEW safety complaints or workplace hazards.\n"
        "3. OPPORTUNITY: Use for finding jobs, training, or SHGs.\n"
        "4. WRITER: Use for greetings, general talk, or if a specialist has already finished their report.\n"
        "5. CRITICAL: If you see a 'SUMMARY' or 'REPORT' in the history, the task is DONE. Route to WRITER.\n"
        "6. END: Only use if the user says goodbye.\n\n"
        "Specialist context available: " + 
        str([m.content for m in state['messages'] if 'REPORT' in m.content or 'SUMMARY' in m.content])
    )

    # 3. Call the Decision Maker
    messages = [{"role": "system", "content": system_prompt}] + state["messages"]
    decision = structured_llm.invoke(messages)
    
    logger.info(f"🧠 Supervisor Path: {decision.next_agent} | {decision.reasoning}")

    return {
        "next_agent": decision.next_agent
    }