# app/graph/nodes/supervisor.py
from app.graph.state import AgentState

def supervisor_node(state: AgentState):
    """
    The supervisor node. 
    It ensures the state is passed to the graph_router for decision making.
    """
    user_id = state.get("user_id", "Unknown Worker")
    
    # Loud Logging: Helpful for debugging the 'Full Phase' testing from WhatsApp
    print(f"🤖 Supervisor: System active for worker {user_id}")

    return state