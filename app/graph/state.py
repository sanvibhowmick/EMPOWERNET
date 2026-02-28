# app/graph/state.py

from typing import Annotated, Sequence, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The unified state for the EmpowerNet Swarm.
    Tracks conversation history and hierarchical user context.
    """
    
    # 1. Conversation History
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # 2. User Core Info
    user_id: str
    user_name: Optional[str]
    preferred_lang: Optional[str]  # e.g., 'Bengali', 'Hindi', 'English'

    # 3. Hierarchical Location (Selected via WhatsApp menus)
    district: Optional[str]        # e.g., '24 PARGANAS NORTH'
    block: Optional[str]           # e.g., 'AMDANGA'
    village: Optional[str]         # e.g., 'ADHATA'
    
    # 4. Professional Context
    user_skills: Optional[str]
    skill_level: Optional[str]     # 'Unskilled', 'Semi-Skilled', 'Skilled', 'Highly Skilled'
    
    # 5. Technical Context
    lat: Optional[float]           # Optional backup for geo-fencing
    lon: Optional[float]
    
    # 6. Routing Context
    next_agent: Optional[str]