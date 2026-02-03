import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage
from app.graph.state import AgentState

logger = logging.getLogger(__name__)

def writer_node(state: AgentState):
    """
    Final Persona Node: Translates and formats technical specialist data 
    into simple, everyday language in the user's specific language and script.
    """
    messages = state.get("messages", [])
    
    # Identify if the last message is a specialist report or a direct user message (for greetings)
    last_msg_content = messages[-1].content if messages else ""
    
    user_name = state.get("user_name", "Friend")
    language = state.get("preferred_lang", "Bengali")
    script = state.get("preferred_script", "Native") 
    location = state.get("location_name", "your area")

    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    # Final Persona Prompt
    persona_prompt = f"""
    You are the EmpowerNet Assistant, a supportive companion for workers in West Bengal.
    Your job is to take the technical data provided and explain it like a helpful neighbor.

    USER CONTEXT:
    - Target Language: {language}
    - Target Script: {script} (IMPORTANT: If 'Native', use {language} script. If 'English', use English script.)
    - User Name: {user_name}
    - User Location: {location}

    TECHNICAL DATA / INPUT:
    {last_msg_content}

    STRICT INSTRUCTIONS:
    1. LANGUAGE: Respond strictly in {language} using {script} script.
    2. SIMPLICITY: Replace all jargon. 
       - Instead of 'Minimum Wage', say 'the lowest pay allowed by law'.
       - Instead of 'Maternity Benefit', say 'support for new mothers'.
       - Instead of 'Geospatial Match', say 'found a place near you'.
    3. GREETING LOGIC: If the input is just a greeting (e.g., 'Hi', 'Hello'), welcome {user_name} and briefly mention that you can help with:
       - Finding local jobs or training.
       - Explaining labor laws and rights.
       - Reporting safety issues in {location}.
    4.If reporting safety issues, thank the user for speaking up and assure them that their concern is important and helpful for other workers
    5. TONE: Warm, encouraging, and respectful. Avoid sounding like a lawyer or a robot.
    6. LENGTH: Keep it under 150 words. Use bullet points for jobs or training lists.
    """

    logger.info(f"✍️ Writer Node: Formatting response for {user_name} in {language} ({script})")
    
    # 1. Generate the final polished response
    response = llm.invoke(persona_prompt)
    
    # 2. Return the final message to the state.
    # We do NOT set a 'next_agent' here because the graph should end at the Writer.
    return {
        "messages": [AIMessage(content=response.content)]
    }