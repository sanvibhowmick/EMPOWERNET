from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal
from app.graph.state import AgentState

# 1. Define the 7 Agents + sakhi + end
class RouterResponse(BaseModel):
    """The routing decision for the VESTA supervisor."""
    next_step: Literal[
        "vakil", "durga", "guru", "sakhi", "sangini", "udyami", "chaukas", "end"
    ] = Field(
        description="The next specialized agent to act based on the user's needs."
    )

def graph_router(state: AgentState) -> Literal["vakil", "durga", "guru", "sakhi", "sangini", "udyami", "chaukas", "end"]:
    """
    Analyzes conversation history and selects the correct specialized agent node.
    Renamed to 'graph_router' to fix the builder.py ImportError.
    """
    messages = state.get("messages", [])
    if not messages:
        return "end"

    # --- FINANCIAL SHIELD: Hardcoded Keyword Logic (Fast & Free) ---
    last_msg = messages[-1].content.lower()
    
    # 1. Emergency Fast-Pass
    if any(word in last_msg for word in ["help", "save", "danger", "police", "sos", "bachao"]):
        return "durga"
    
    # 2. Simple Keyword Mapping
    if any(word in last_msg for word in ["salary", "wage", "law", "taka", "paisa"]):
        return "vakil"
    if any(word in last_msg for word in ["job", "work", "earn", "kaaj"]):
        return "sangini"
    if any(word in last_msg for word in ["loan", "shg", "group", "business"]):
        return "udyami"

    # --- LLM FALLBACK: For complex reasoning ---
    # Enforced max_tokens=100 for cost-effectiveness
    llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=100) 
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the VESTA Supervisor. Route the user based on these definitions:
        - 'vakil': Legal rights, minimum wage, or labor laws.
        - 'durga': EMERGENCY/SOS, distress, or immediate threats.
        - 'guru': Education, government skill training (Utkarsh Bangla).
        - 'sakhi': Finding safety sisters or general help.
        - 'sangini': Job finding and workplace recommendations.
        - 'udyami': Micro-loans, SHG financing, or business setup.
        - 'chaukas': Reporting unsafe areas or workplace safety.
        - 'end': If the user is saying goodbye or the task is finished."""),
        ("placeholder", "{messages}"),
    ])
    
    supervisor = prompt | llm.with_structured_output(RouterResponse)
    
    try:
        response = supervisor.invoke(state)
        return response.next_step
    except Exception:
        # Final safety fallback
        return "sakhi"