import os
import logging
import sys
from fastapi import FastAPI, Request, Response, BackgroundTasks
from dotenv import load_dotenv
from openai import OpenAI
from langchain_core.messages import HumanMessage

# 1. IMMEDIATE FINANCIAL CHECK
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key or not api_key.startswith("sk-"):
    print("❌ FATAL: OPENAI_API_KEY is missing or invalid. Shutdown initiated to save costs.")
    sys.exit(1)

app = FastAPI(title="EmpowerNet Secure Multi-Agent Backend")
client = OpenAI(api_key=api_key)

# Configure "Loud Logging"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- ANTI-RETRY SHIELD ---
PROCESSED_MESSAGE_IDS = []

# --- 1. THE PROTECTED BACKGROUND SWARM ---
async def run_empowernet_swarm(user_data):
    """The EmpowerNet Brain Room."""
    user_id = str(user_data["sender"])
    user_input = user_data["content"]
    msg_id = user_data.get("id", "unknown")

    try:
        # Import the correctly named swarm and tools
        from app.graph.builder import empower_swarm
        from app.api.whatsapp import send_whatsapp_message
        
        # B. THE SWARM EXECUTION (WITH COST-CONTROL)
        config = {
            "configurable": {
                "thread_id": user_id,
            }, 
            "recursion_limit": 10  # Slightly higher to allow Memory -> Supervisor -> Specialist -> Supervisor -> Writer
        }
        
        # Detect initial language (Memory Node will refine this further)
        # Default to Bengali for rural West Bengal context unless greeting in English
        initial_lang = "English" if any(word in user_input.lower() for word in ["hi", "hello", "help"]) else "Bengali"
        
        # SYNC RULE: Language = Script
        initial_script = "Native" if initial_lang != "English" else "English"

        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_id": user_id,
            "preferred_lang": initial_lang,
            "preferred_script": initial_script,
            "next_agent": "memory" # Start at memory node
        }

        # C. SWARM EXECUTION
        logger.info(f"🚀 EmpowerNet Swarm triggered for {user_id} | Msg ID: {msg_id}")
        final_state = empower_swarm.invoke(initial_state, config=config)
        
        # D. DIRECT DELIVERY
        # The final message from the Writer node
        final_message = final_state["messages"][-1].content
        
        await send_whatsapp_message(user_id, final_message)
        logger.info(f"🏁 [SUCCESS] Interaction {msg_id} complete.")

    except Exception as e:
        error_msg = str(e).lower()
        if "recursion" in error_msg:
            logger.error(f"🛑 Loop detected for ID {msg_id}. Terminating swarm.")
        else:
            logger.error(f"❌ [CRITICAL] Swarm failed for {msg_id}: {str(e)}", exc_info=True)

# --- 2. WEBHOOK ENDPOINTS ---
@app.get("/webhook")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return Response(content=request.query_params.get("hub.challenge"), media_type="text/plain")
    return Response(content="Forbidden", status_code=403)

@app.post("/webhook")
async def main_entry(request: Request, background_tasks: BackgroundTasks):
    from app.api.whatsapp import handle_whatsapp_message
    user_data = await handle_whatsapp_message(request)
    
    if user_data:
        msg_id = user_data.get("id")

        if msg_id in PROCESSED_MESSAGE_IDS:
            logger.info(f"🚫 Blocking duplicate retry for ID: {msg_id}")
            return {"status": "success"}

        PROCESSED_MESSAGE_IDS.append(msg_id)
        if len(PROCESSED_MESSAGE_IDS) > 200:
            PROCESSED_MESSAGE_IDS.pop(0)

        # START BACKGROUND THINKING
        background_tasks.add_task(run_empowernet_swarm, user_data)
        
        # RETURN SUCCESS INSTANTLY
        return {"status": "success"}

    return {"status": "ignored"}