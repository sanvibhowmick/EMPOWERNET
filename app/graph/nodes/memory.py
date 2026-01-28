from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from app.graph.state import AgentState
from app.tools.memory import upsert_user_profile, get_user_context

class ExtractedInfo(BaseModel):
    """The data we want to remember about the user."""
    name: str = Field(None, description="The user's name")
    language: str = Field(None, description="Preferred language (Bengali, Hindi, English)")
    skills: str = Field(None, description="Skills or job types mentioned")

def memory_node(state: AgentState):
    """
    1. Extracts facts from the latest message.
    2. Syncs them to the database.
    3. UPDATES THE STATE so other nodes can see it.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    last_user_msg = messages[-1].content
    
    # Use gpt-4o-mini for fast extraction
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0).with_structured_output(ExtractedInfo)
    
    # 1. Extract new info
    new_info = llm.invoke(f"User says: {last_user_msg}. Extract name, language, or skills.")
    
    # 2. Sync to DB if we found anything
    if new_info.name or new_info.language or new_info.skills:
        upsert_user_profile.invoke({
            "phone_number": user_id,
            "name": new_info.name,
            "language": new_info.language,
            "skills": new_info.skills
        })
    
    # 3. CRITICAL FIX: Return the values to update the AgentState
    # We also pull existing context from DB in case this is a returning user
    db_profile = get_user_context.invoke({"phone_number": user_id})
    
    return {
        "user_name": new_info.name or db_profile.get("name"),
        "preferred_lang": new_info.language or db_profile.get("language"),
        "user_skills": new_info.skills or db_profile.get("skills")
    }