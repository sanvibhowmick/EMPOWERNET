from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.tools.training import get_nearby_training
from app.tools.memory import get_user_context
from app.graph.state import AgentState

def guru_node(state: AgentState):
    """
    The Guru node. Uses AI to map user intent to specific labor categories 
    (Agriculture, Bakery, Construction, etc.) from uploaded documents.
    """
    user_id = state.get("user_id")
    messages = state.get("messages", [])
    
    # 1. AI Intent Extraction matched to your specific categories
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    last_user_msg = next((m.content for m in reversed(messages) if m.type == "human"), "")
    
    # We guide the AI to use the specific categories found in your employment PDFs
    extraction_prompt = (
        "Analyze the user's message and map their interest to exactly ONE of these "
        "categories: 'Agriculture', 'Bakery', 'Construction', 'Road Maintenance', "
        "or 'Establishment'.\n"
        "If the user mentions sewing or stitching, use 'Establishment'.\n"
        "Return ONLY the category name. If it does not fit these, return 'General'.\n\n"
        f"User Message: {last_user_msg}"
    )
    
    ai_extracted_category = llm.invoke(extraction_prompt).content.strip()
    category_filter = None if ai_extracted_category == "General" else ai_extracted_category

    # 2. Get Dynamic Location from Profile Tool
    profile = get_user_context.invoke({"phone_number": user_id})
    user_lat, user_lon = profile.get("lat"), profile.get("lon")

    print(f"🎓 Guru AI mapped intent to category: {ai_extracted_category}")

    # 3. Call the Tool with the specific category
    training_options = get_nearby_training.invoke({
        "user_lat": user_lat, 
        "user_lon": user_lon,
        "category": category_filter
    })

    # 4. Formulate Response
    response = (
        f"I see you're interested in opportunities within the **{ai_extracted_category}** sector. "
        f"I found these nearby training programs to help you grow:\n\n"
        f"{training_options}\n\n"
        "Do you want to register for one of these?"
    )

    return {
        "messages": [AIMessage(content=response)],
        "next_agent": "supervisor"
    }