from langchain_core.messages import AIMessage
from app.tools.spatial import get_nearby_safety_resources  # Fixed import
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def sakhi_node(state: AgentState):
    """
    The Sakhi (Safety Sister) node.
    Uses the fixed spatial tool to coordinate community-based safety.
    """
    # 1. Get Dynamic Identity from State
    user_id = state.get("user_id")
    
    # 2. Get Dynamic Location from DB (No Hardcoding)
    profile = get_user_context.invoke({"phone_number": user_id})
    user_lat = profile.get("lat")
    user_lon = profile.get("lon")

    print(f"🕵️‍♀️ Sakhi Agent: Activating community safety net for {user_id}...")

    # 3. Call the tool using its new name from spatial.py
    # We pass the coordinates retrieved from the user's profile
    nearby_resources = get_nearby_safety_resources.invoke({
        "user_lat": user_lat, 
        "user_lon": user_lon,
        "radius_km": 1.5  # Slightly wider radius for preventative safety
    })

    response = (
        "I am here with you. I have identified the nearest safety resources and "
        "sisters in your village:\n\n"
        f"{nearby_resources}\n\n"
        "Would you like me to alert a 'Safety Sister' that you are walking home, "
        "or should I stay on the line until you reach safely?"
    )

    return {
        "messages": [AIMessage(content=response)],
        "next_agent": "supervisor"
    }