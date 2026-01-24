from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    """
    The state of the VESTA agent graph.
    """
    # 'add_messages' is a reducer. It tells LangGraph to append new messages 
    # to the existing list so the agents remember the full conversation.
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # This string tracks which agent should act next (e.g., "Vakil", "Durga", or "END")
    next_agent: str
    
    # Optional: Track if an SOS was triggered to keep the UI alerted
    emergency_mode: bool