# app/graph/nodes/supervisor.py
from app.graph.state import AgentState

def supervisor_node(state: AgentState):
    """
    The supervisor node doesn't need to 'do' much because 
    the graph_router logic handles the decision making.
    It just ensures the state is passed along.
    """
    return state