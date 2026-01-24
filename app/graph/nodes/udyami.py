from langchain_core.messages import AIMessage
from app.tools.community import get_nearby_shgs
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def udyami_node(state: AgentState):
    """
    The Udyami node.
    Dynamically retrieves user location and connects them to nearby SHGs.
    """
    # 1. Get the unique identifier for the user (WhatsApp Number)
    user_id = state.get("user_id")
    
    print(f"💰 Udyami Agent: Accessing profile for {user_id}...")

    # 2. Retrieve live location from the Database
    # This ensures we search near where she is RIGHT NOW
    profile = get_user_context.invoke({"phone_number": user_id})
    
    # Extract coordinates (retrieved as a dict from your PostGIS-enabled DB)
    user_lat = profile.get("lat")
    user_lon = profile.get("lon")

    if not user_lat or not user_lon:
        return {
            "messages": [AIMessage(content="I couldn't find your location. Please share your location on WhatsApp so I can find groups near you.")],
            "next_agent": "supervisor"
        }

    # 3. Call the Community Tool with real data
    shg_connections = get_nearby_shgs.invoke({
        "user_lat": user_lat, 
        "user_lon": user_lon
    })

    # 4. Formulate the response
    response = (
        "To help you start or grow your business, I have found these nearby "
        "Self-Help Groups (SHGs) in your area:\n\n"
        f"{shg_connections}\n\n"
        "Would you like me to explain how to join one of these groups?"
    )

    return {
        "messages": [AIMessage(content=response)],
        "next_agent": "supervisor"
    }