import os
import httpx
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

async def download_whatsapp_media(media_id):
    """Downloads media from Meta and saves it locally for Whisper."""
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        # Step 1: Get the media URL from Meta (Updated to v21.0)
        url_res = await client.get(f"https://graph.facebook.com/v21.0/{media_id}", headers=headers)
        media_url = url_res.json().get("url")
        
        if not media_url:
            logger.error(f"❌ Failed to get media URL for ID: {media_id}")
            return None

        # Step 2: Download the actual file
        media_res = await client.get(media_url, headers=headers)
        temp_filename = f"temp_{uuid.uuid4()}.ogg"
        
        with open(temp_filename, "wb") as f:
            f.write(media_res.content)
    
    return temp_filename

async def handle_whatsapp_message(request: Request):
    """Parses incoming WhatsApp JSON and extracts sender, content, and ID."""
    data = await request.json()
    
    try:
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message = value['messages'][0]
            user_phone = message.get('from')
            msg_id = message.get('id')

            # --- 1. TEXT HANDLING ---
            if message.get('type') == 'text':
                user_input = message['text'].get('body')
                return {"id": msg_id, "sender": user_phone, "content": user_input}
            
            # --- 2. LOCATION HANDLING (New Feature) ---
            elif message.get('type') == 'location':
                loc = message['location']
                lat, lon = loc.get('latitude'), loc.get('longitude')
                # Formatted text so the swarm agents can process the coordinates
                user_input = f"My current location is Latitude: {lat}, Longitude: {lon}"
                return {"id": msg_id, "sender": user_phone, "content": user_input}
            
            # --- 3. AUDIO HANDLING ---
            elif message.get('type') == 'audio':
                media_id = message['audio'].get('id')
                file_path = await download_whatsapp_media(media_id)
                
                if file_path:
                    try:
                        # Process transcription
                        transcribed_text = transcribe_audio(file_path)
                        return {"id": msg_id, "sender": user_phone, "content": transcribed_text}
                    finally:
                        # Robust cleanup: Ensure file is deleted even if transcription fails
                        if os.path.exists(file_path):
                            os.remove(file_path)
                
    except Exception as e:
        logger.error(f"❌ Webhook Parsing Error: {e}")
    
    return None

async def send_whatsapp_message(to, text):
    """Pushes VESTA's output back to the user via async httpx."""
    # Updated to v21.0
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
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
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            logger.info(f"📡 Meta Delivery Report: {response.status_code} - {response.text}")
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp message: {e}")
            return None