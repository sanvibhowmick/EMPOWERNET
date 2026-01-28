from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from app.graph.state import AgentState
import re

def writer_node(state: AgentState, config: RunnableConfig):
    # 1. Identify the latest message
    user_msgs = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    latest_input = user_msgs[-1].content.strip() if user_msgs else "Hi"
    technical_report = state["messages"][-1].content
    user_name = state.get("user_name") or "Sister"
    
    # 2. Logic: Treat Script and Language as Same
    # If it looks like English script, it's English. Otherwise, it's the saved local language.
    is_english = bool(re.fullmatch(r"^[a-zA-Z0-9\s\.,!?']+$", latest_input))
    
    # Sync target to user input or database preference
    target_unit = "English" if is_english else (state.get("language") or "Bengali")

    # 3. Model Configuration
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

    # 4. Strict Identity and Unit Prompt
    system_instructions = (
        f"IDENTITY: Your name is EmpowerNet.\n\n"
        f"STRICT RULE: You are speaking in {target_unit}.\n"
        f"1. If {target_unit} is English: Write ONLY in standard English.\n"
        f"2. If {target_unit} is Bengali: Write ONLY in Bengali script (বাংলা).\n"
        f"3. If {target_unit} is Hindi: Write ONLY in Devanagari script (नमस्ते).\n"
        "4. NEVER use English letters to write Bengali or Hindi words. No transliteration." \
        "Remember you are talking to rural women use simple terms and not technical jargon. and complex vocabulary\n"
    )

    prompt_content = (
        f"User Name: {user_name}\n"
        f"Technical Data: {technical_report}\n\n"
        f"Task: Respond as EmpowerNet in {target_unit} using its native script."
    )

    # 5. Invoke
    final_voice = llm.invoke([
        SystemMessage(content=system_instructions),
        HumanMessage(content=prompt_content)
    ]).content

    return {"messages": [AIMessage(content=final_voice)]}