# app/graph/nodes/memory.py
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from app.graph.state import AgentState
from app.tools.memory import upsert_user_profile

class UserFact(BaseModel):
    """Information extracted from conversation."""
    name: str = Field(None, description="The user's name")
    language: str = Field(None, description="Preferred language (Bengali/Hindi/English)")
    skills: str = Field(None, description="Skills mentioned (e.g., tailor, cook, helper)")

def memory_node(state: AgentState):
    """Silently harvests facts from the user's message and saves to DB."""
    user_id = state.get("user_id")
    last_msg = state["messages"][-1].content
    
    # Extraction Step (Low cost model)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(UserFact)
    facts = llm.invoke(f"Extract profile facts from: {last_msg}")
    
    # If facts found, update DB
    if facts.name or facts.language or facts.skills:
        upsert_user_profile.invoke({
            "phone_number": user_id,
            "name": facts.name,
            "language": facts.language,
            "skills": facts.skills
        })
        print(f"🧠 Memory: Updated profile for {user_id}")
    
    return state