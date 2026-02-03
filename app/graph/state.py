from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The unified state for the EmpowerNet Swarm.
    Tracks conversation history and user-specific context across all nodes.
    """
    
   
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
 
    user_id: str
    user_name: Optional[str]
    preferred_lang: Optional[str]

    user_skills: Optional[str]
    
   
    lat: Optional[float]
    lon: Optional[float]
    location_name: Optional[str] 
    
   
    next_agent: Optional[str]