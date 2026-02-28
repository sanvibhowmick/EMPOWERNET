# main.py

import os
import logging
import sys
import httpx
from fastapi import FastAPI, Request, Response, BackgroundTasks
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

# 1. INITIALIZATION & SECURITY CHECK
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key or not api_key.startswith("sk-"):
    print("❌ FATAL: OPENAI_API_KEY is missing or invalid. Shutdown initiated.")
    sys.exit(1)

app = FastAPI(title="EmpowerNet Secure Multi-Agent Backend")

# Configure Logging for production visibility
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# --- ANTI-RETRY SHIELD ---
# Stores processed Meta message IDs to prevent double-processing during network lag
PROCESSED_MESSAGE_IDS = set()

# --- 1. THE PROTECTED BACKGROUND SWARM ---
async def run_empowernet_swarm(user_data: dict):
    """
    The EmpowerNet Brain Room: Runs the LangGraph swarm in the background.
    """
    user_id = str(user_data["sender"])
    user_input = user_data["content"]
    msg_id = user_data.get("id", "unknown")

    try:
        from app.graph.builder import empower_swarm
        from app.api.whatsapp import send_whatsapp_message, send_whatsapp_list
        
        # A. SWARM CONFIGURATION
        # thread_id ensures persistent memory for this specific phone number
        config = {
            "configurable": {"thread_id": user_id}, 
            "recursion_limit": 15 
        }
        
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "user_id": user_id,
        }

        # B. SWARM EXECUTION
        logger.info(f"🚀 Swarm triggered for {user_id} | Msg ID: {msg_id}")
        final_state = empower_swarm.invoke(initial_state, config=config)
        
        # C. DELIVERY LOGIC: LIST (Dropdown) vs TEXT
        # We check the final message from the Writer node for UI signals
        final_msg_node = final_state["messages"][-1]
        final_text = final_msg_node.content
        
        if "LIST_REQUEST" in final_text:
            logger.info(f"📋 Intercepting LIST_REQUEST UI signal for {user_id}")
            
            # Extract dropdown metadata from additional_kwargs provided by the Writer
            list_type = final_text.split(":")[1] # DISTRICT, BLOCK, or VILLAGE
            rows = final_msg_node.additional_kwargs.get("rows", [])
            body_text = final_msg_node.additional_kwargs.get("body", "Please select an option:")
            
            # Format the sections for Meta Interactive List API
            sections = [{
                "title": f"Select {list_type.capitalize()}",
                "rows": rows
            }]
            
            await send_whatsapp_list(
                to=user_id, 
                body_text=body_text, 
                button_label=f"View {list_type.capitalize()}s", 
                sections=sections
            )
        else:
            # Standard Text Delivery (Advice, Job Lists, or Reports)
            logger.info(f"✉️ Sending Standard Text Response to {user_id}")
            await send_whatsapp_message(user_id, final_text)

        logger.info(f"🏁 [SUCCESS] Interaction {msg_id} complete.")

    except Exception as e:
        logger.error(f"❌ [CRITICAL] Swarm failed for {msg_id}: {str(e)}", exc_info=True)

# --- 2. WEBHOOK ENDPOINTS ---

@app.get("/webhook")
async def verify_webhook(request: Request):
    """Meta verification endpoint for webhook setup."""
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return Response(content=request.query_params.get("hub.challenge"), media_type="text/plain")
    return Response(content="Forbidden", status_code=403)

@app.post("/webhook")
async def main_entry(request: Request, background_tasks: BackgroundTasks):
    """
    Main entry point for all WhatsApp interactions. 
    Acknowledges Meta instantly and processes the AI in the background.
    """
    from app.api.whatsapp import handle_whatsapp_message
    
    user_data = await handle_whatsapp_message(request)
    
    if user_data:
        msg_id = user_data.get("id")

        # Deduplication Guard
        if msg_id in PROCESSED_MESSAGE_IDS:
            logger.info(f"🚫 Blocking duplicate retry for ID: {msg_id}")
            return {"status": "success"}

        PROCESSED_MESSAGE_IDS.add(msg_id)
        
        # Memory cleanup: Keep the last 500 IDs to avoid memory bloat
        if len(PROCESSED_MESSAGE_IDS) > 500:
            PROCESSED_MESSAGE_IDS.pop()

       
        background_tasks.add_task(run_empowernet_swarm, user_data)
        
        return {"status": "success"}

    return {"status": "ignored"}