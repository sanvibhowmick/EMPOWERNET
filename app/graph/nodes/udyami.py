from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from app.tools.community import get_nearby_shgs
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def udyami_node(state: AgentState, config: RunnableConfig):
    """
    The Udyami node.
    Dynamically retrieves user location and connects them to nearby SHGs 
    while enforcing strict token limits.
    """
    # 1. Get the unique identifier for the user (WhatsApp Number)
    user_id = state.get("user_id")
    
    print(f"💰 Udyami Agent: Accessing profile for {user_id}...")

    # 2. Retrieve live location from the Database
    profile = get_user_context.invoke({"phone_number": user_id})
    
    user_lat = profile.get("lat")
    user_lon = profile.get("lon")

    if not user_lat or not user_lon:
        return {
            "messages": [AIMessage(content="I couldn't find your location. Please share your location on WhatsApp so I can find groups near you.")],
            "next_agent": "supervisor"
        }

    # 3. Financial Shield: Extract token limit from config
    # Reads 'max_tokens' (400) from your main.py config
    limit = config.get("configurable", {}).get("max_tokens", 400)
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_tokens=limit)

    # 4. Call the Community Tool with real data
    shg_connections = get_nearby_shgs.invoke({
        "user_lat": user_lat, 
        "user_lon": user_lon
    })

    # 5. Formulate the response [cite: uploaded:sanvibhowmick/vesta/VESTA-0460c0fcf20d22d8c5e17b96bf721b19