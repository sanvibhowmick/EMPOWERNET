import os
import logging
import sys
from fastapi import FastAPI, Request, Response, BackgroundTasks
from dotenv import load_dotenv
from openai import OpenAI

# 1. IMMEDIATE FINANCIAL CHECK: Stop the server if the key is missing
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key or not api_key.startswith("sk-"):
    print("❌ FATAL: OPENAI_API_KEY is missing or invalid. Shutdown initiated to save costs.")
    sys.exit(1)

app = FastAPI(title="VESTA Secure Multi-Agent Backend")
client = OpenAI(api_key=api_key)

# Configure "Loud Logging" to catch silent background crashes
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Anti-Retry Memory: Keeps track of message IDs for 5 minutes
PROCESSED_MESSAGE_IDS = set()

# --- 1. THE 'DIDI' REFINER (LOW-COST MODEL) ---
def refine_for_user(raw_agent_output, original_user_query):
    """Summarizes specialist output using GPT-4o-mini to save money."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 90% cheaper than GPT-4o
            messages=[
                {"role": "system", "content": "You are VESTA Didi. Summarize this simply in Benglish/Hindi."},
                {"role": "user", "content": f"User query: {original_user_query}\nAgent data: {raw_agent_output}"}
            ],
            max_tokens=250 # CAP 1: Limits the cost of the final response
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"❌ Refinement Error: {e}")
        return raw_agent_output

# --- 2. THE PROTECTED BACKGROUND SWARM ---
async def run_vesta_swarm(user_data):
    """The brain room. Protected by a recursion limit and token caps."""
    user_id = user_data["sender"]
    user_input = user_data["content"]
    msg_id = user_data.get("id", "unknown")

    try:
        from app.graph.builder import vesta_swarm
        from app.api.whatsapp import send_whatsapp_message

        # A. Handshake: Let the user know we are working
        send_whatsapp_message(user_id, "Sunte paachhi... let me check that for you. 🧐")

        # B. THE SWARM EXECUTION (WITH COST-CONTROL)
        # We increase recursion to 8 so it can finish, but keep tokens tight.
        config = {
            "configurable": {
                "thread_id": user_id,
                "max_tokens": 400 # CAP 2: Stops specialists from 'reading' too much
            }, 
            "recursion_limit": 8  # CAP 3: Kill the swarm if it loops like the 'Bakery' issue
        }
        
        initial_state = {
            "messages": [{"role": "user", "content": user_input}],
            "user_id": user_id
        }

        # The Swarm 'Thinks' here
        final_state = vesta_swarm.invoke(initial_state, config=config)
        raw_output = final_state["messages"][-1].content
        
        # C. Refine with Didi and Send
        final_message = refine_for_user(raw_output, user_input)
        send_whatsapp_message(user_id, final_message)
        logger.info(f"🏁 [SUCCESS] Interaction {msg_id} complete.")

    except Exception as e:
        logger.error(f"❌ [CRITICAL] Swarm failed for {msg_id}: {str(e)}", exc_info=True)

# --- 3. WEBHOOK ENDPOINTS ---
@app.get("/webhook")
@app.get("/webhook/")
async def verify_webhook(request: Request):
    if request.query_params.get("hub.verify_token") == os.getenv("VERIFY_TOKEN"):
        return Response(content=request.query_params.get("hub.challenge"), media_type="text/plain")
    return Response(content="Forbidden", status_code=403)

@app.post("/webhook")
@app.post("/webhook/")
async def main_entry(request: Request, background_tasks: BackgroundTasks):
    """Instant-response entry point to block Meta retries."""
    from app.api.whatsapp import handle_whatsapp_message
    user_data = await handle_whatsapp_message(request)
    
    if user_data:
        msg_id = user_data.get("id")

        # --- THE ANTI-RETRY SHIELD ---
        # If Meta resends a message while we are still thinking, this kills it instantly.
        if msg_id in PROCESSED_MESSAGE_IDS:
            logger.info(f"🚫 Blocking duplicate retry for ID: {msg_id}")
            return {"status": "success"} # Still return 200 so Meta stops retrying

        PROCESSED_MESSAGE_IDS.add(msg_id)
        if len(PROCESSED_MESSAGE_IDS) > 200:
            PROCESSED_MESSAGE_IDS.clear() # Prevent memory bloat

        # START BACKGROUND THINKING
        background_tasks.add_task(run_vesta_swarm, user_data)
        
        # RETURN SUCCESS INSTANTLY (Meta expects this in < 3 seconds)
        return {"status": "success"}

    return {"status": "ignored"}