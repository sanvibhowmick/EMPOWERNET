from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import Literal
from app.graph.state import AgentState

# 1. Define the 7 Agents + General + FINISH
class RouterResponse(BaseModel):
    """The routing decision for the VESTA supervisor."""
    next_step: Literal[
        "vakil", "durga", "guru", "sakhi", "sangini", "udyami", "chaukas", "general", "FINISH"
    ] = Field(
        description="The next specialized agent to act based on the user's needs."
    )

def get_supervisor_router(state: AgentState):
    """
    Analyzes conversation history and selects the correct specialized agent node.
    """
    # ENFORCED: Added max_tokens=100 to ensure the gpt-4o model remains cost-effective and avoids 'yapping'
    llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=100) 
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are the VESTA Supervisor, an expert at directing informal workers to the right 'Digital Didi' agent.
        
        Route the user based on these strict definitions:
        - 'vakil': Legal rights, minimum wage audits, or labor law questions.
        - 'durga': EMERGENCY/SOS. Use this if you detect distress, danger, or immediate safety threats.
        - 'guru': Education, government skill training (Utkarsh Bangla), or learning opportunities.
        - 'sakhi': Finding a 'Safety Sister' to walk home with or locating women nearby.
        - 'sangini': Finding jobs vetted by the community or workplace recommendations.
        - 'udyami': Micro-loans, Self-Help Group (SHG) financing, or business setup.
        - 'chaukas': Reporting unsafe areas, flagging red zones, or workplace safety reviews.
        - 'general': Greetings, how-to-use VESTA, or casual conversation.
        - 'FINISH': Only when the user explicitly says goodbye or the task is fully complete."""),
        ("placeholder", "{messages}"),
    ])
    
    # Force the router to provide a valid agent name from the list
    supervisor = prompt | llm.with_structured_output(RouterResponse)
    
    # Process the state to get the decision
    response = supervisor.invoke(state)
    return response.next_step