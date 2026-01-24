import os
import requests
import uuid
import logging
from fastapi import APIRouter, Request
from app.core.whisper import transcribe_audio

router = APIRouter()
logger = logging.getLogger(__name__)

# Constants
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

def download_whatsapp_media(media_id):
    """Downloads media from Meta and saves it locally for Whisper."""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    # Step 1: Get the media URL from Meta
    url_res = requests.get(f"https://graph.facebook.com/v18.0/{media_id}", headers=headers)
    media_url = url_res.json().get("url")
    
    if not media_url:
        logger.error(f"❌ Failed to get media URL for ID: {media_id}")
        return None

    # Step 2: Download the actual file
    media_res = requests.get(media_url, headers=headers)
    temp_filename = f"temp_{uuid.uuid4()}.ogg"
    
    with open(temp_filename, "wb") as f:
        f.write(media_res.content)
    
    return temp_filename

async def handle_whatsapp_message(request: Request):
    """Parses incoming WhatsApp JSON and extracts the sender, content, and ID."""
    data = await request.json()
    
    try:
        # Navigate the Meta JSON structure
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message = value['messages'][0]
            user_phone = message.get('from')
            msg_id = message.get('id') # CRITICAL: Needed for the Duplicate Shield

            # --- TEXT HANDLING ---
            if message.get('type') == 'text':
                user_input = message['text'].get('body')
                return {"id": msg_id, "sender": user_phone, "content": user_input}
            
            # --- AUDIO HANDLING ---
            elif message.get('type') == 'audio':
                media_id = message['audio'].get('id')
                file_path = download_whatsapp_media(media_id)
                
                if file_path:
                    transcribed_text = transcribe_audio(file_path)
                    os.remove(file_path) # Clean up
                    return {"id": msg_id, "sender": user_phone, "content": transcribed_text}
                
    except Exception as e:
        logger.error(f"❌ Webhook Parsing Error: {e}")
    
    return None

def send_whatsapp_message(to, text):
    """Pushes VESTA's output back to the user with loud logging for debugging."""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}", 
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        # --- THE LOUD DEBUGGER ---
        # This will tell us if the token is expired or the number isn't whitelisted
        logger.info(f"📡 Meta Delivery Report: {response.status_code} - {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"❌ Failed to send WhatsApp message: {e}")
        return None