# app/api/whatsapp.py

import os
import httpx
import uuid
import logging
from fastapi import Request
from app.core.whisper import transcribe_audio

logger = logging.getLogger(__name__)

# Constants - Ensure these are in your .env
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

async def download_whatsapp_media(media_id: str):
    """
    Downloads media from Meta Graph API (v21.0) and saves it locally.
    Used for processing audio messages via Whisper.
    """
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: Get the media URL
            url_res = await client.get(
                f"https://graph.facebook.com/v21.0/{media_id}", 
                headers=headers
            )
            media_url = url_res.json().get("url")
            
            if not media_url:
                logger.error(f"❌ Failed to get media URL for ID: {media_id}")
                return None

            # Step 2: Download the binary file
            media_res = await client.get(media_url, headers=headers)
            temp_filename = f"temp_audio_{uuid.uuid4()}.ogg"
            
            with open(temp_filename, "wb") as f:
                f.write(media_res.content)
            
            return temp_filename
        except Exception as e:
            logger.error(f"❌ Media Download Error: {e}")
            return None

async def handle_whatsapp_message(request: Request):
    """
    Parses incoming Meta Webhook JSON. 
    Supports: Text, Location pins, Audio (Voice notes), and Interactive List selection.
    """
    try:
        data = await request.json()
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        
        if 'messages' in value:
            message = value['messages'][0]
            user_phone = message.get('from')
            msg_id = message.get('id')
            msg_type = message.get('type')

            # --- 1. INTERACTIVE LIST REPLY (Dropdowns) ---
            if msg_type == 'interactive':
                interactive_res = message.get('interactive', {})
                if interactive_res.get('type') == 'list_reply':
                    # Extract the 'title' (e.g., 'NORTH 24 PARGANAS' or 'AMDANGA')
                    # This is passed to the Swarm as user input
                    selection = interactive_res['list_reply'].get('title')
                    return {"id": msg_id, "sender": user_phone, "content": selection}

            # --- 2. TEXT MESSAGES ---
            elif msg_type == 'text':
                user_input = message['text'].get('body')
                return {"id": msg_id, "sender": user_phone, "content": user_input}
            
            # --- 3. LOCATION PINS (GPS) ---
            elif msg_type == 'location':
                loc = message['location']
                lat, lon = loc.get('latitude'), loc.get('longitude')
                # Format as text so Memory Node can extract coordinates
                user_input = f"Lat: {lat}, Lon: {lon}"
                return {"id": msg_id, "sender": user_phone, "content": user_input}
            
            # --- 4. AUDIO / VOICE NOTES ---
            elif msg_type == 'audio':
                media_id = message['audio'].get('id')
                file_path = await download_whatsapp_media(media_id)
                if file_path:
                    try:
                        # Transcribe the worker's voice note to text
                        transcribed_text = transcribe_audio(file_path)
                        return {"id": msg_id, "sender": user_phone, "content": transcribed_text}
                    finally:
                        # Cleanup temp file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            
    except Exception as e:
        logger.error(f"❌ Webhook Parsing Error: {e}")
    
    return None

async def send_whatsapp_message(to: str, text: str):
    """
    Sends a standard text message back to the user.
    """
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
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp text: {e}")
            return None

async def send_whatsapp_list(to: str, body_text: str, button_label: str, sections: list):
    """
    Sends an interactive List Message (Dropdown menu).
    Used for District, Block, and Village selection.
    """
    url = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}", 
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_label,
                "sections": sections
            }
        }
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            logger.info(f"📡 Interactive List Sent to {to}")
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to send WhatsApp list: {e}")
            return None