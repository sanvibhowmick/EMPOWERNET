from typing import Annotated, TypedDict, List, Optional
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The central state for the VESTA swarm.
    
    Attributes:
        messages: A list of messages (Human, AI, Tool). 
                  'add_messages' ensures new items are appended, not overwritten.
        user_id: The unique WhatsApp number (e.g., '16315551181').
        preferred_lang: The user's chosen language (Bengali, Hindi, English).
        user_name: Extracted name from 'memory_node'.
        user_skills: Extracted skills (e.g., 'tailor', 'helper').
        lat: Latitude from WhatsApp Location Pin.
        lon: Longitude from WhatsApp Location Pin.
        next_agent: A hint for the supervisor/router to track flow.
    """
    messages: Annotated[List[AnyMessage], add_messages]
    user_id: str
    preferred_lang: Optional[str]
    user_name: Optional[str]
    user_skills: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    next_agent: str