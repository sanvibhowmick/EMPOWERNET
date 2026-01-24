from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.router import get_supervisor_router
from app.graph.nodes.supervisor import supervisor_node
from app.graph.nodes.vakil import vakil_node
from app.graph.nodes.guru import guru_node
from app.graph.nodes.udyami import udyami_node
from app.graph.nodes.sangini import sangini_node
from app.graph.nodes.sakhi import sakhi_node
from app.graph.nodes.chaukas import chaukas_node
from app.graph.nodes.durga import durga_node
from app.core.guard import is_emergency

def graph_router(state: AgentState):
    """
    Decides where the conversation goes next.
    Maps AI router decisions to actual graph nodes.
    """
    messages = state.get("messages", [])
    last_msg = messages[-1].content if messages else ""

    # 1. EMERGENCY BYPASS: Checks for crisis keywords immediately
    if is_emergency(last_msg):
        return "durga"

    # 2. AI ROUTING: Asks the supervisor logic which agent is needed
    next_step = get_supervisor_router(state)
    
    # 3. FIXING THE 'GENERAL' KEYERROR:
    # If the supervisor says 'general' (like for 'hi') or 'FINISH', we go to END.
    if next_step in ["general", "FINISH", "end"]:
        return "end"
    
    return next_step

# --- BUILD THE GRAPH ---

builder = StateGraph(AgentState)

# 1. Register All Nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("vakil", vakil_node)
builder.add_node("guru", guru_node)
builder.add_node("udyami", udyami_node)
builder.add_node("sangini", sangini_node)
builder.add_node("sakhi", sakhi_node)
builder.add_node("chaukas", chaukas_node)
builder.add_node("durga", durga_node)

# 2. Set the starting point
builder.set_entry_point("supervisor")

# 3. ONE-WAY SPECIALIST EDGES (The Financial Shield)
# Once an agent (like Vakil) answers, it finishes. 
# This prevents it from looping back and spending more money.
builder.add_edge("vakil", END)
builder.add_edge("guru", END)
builder.add_edge("udyami", END)
builder.add_edge("sangini", END)
builder.add_edge("sakhi", END)
builder.add_edge("chaukas", END)
builder.add_edge("durga", END)

# 4. Integrate the Conditional Router
builder.add_conditional_edges(
    "supervisor",
    graph_router,
    {
        "vakil": "vakil",
        "guru": "guru",
        "udyami": "udyami",
        "sangini": "sangini",
        "sakhi": "sakhi",
        "chaukas": "chaukas",
        "durga": "durga",
        "end": END # This maps the "end" string from graph_router to the actual END
    }
)

# 5. Compile the Workflow
vesta_swarm = builder.compile()