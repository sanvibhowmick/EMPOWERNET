from langchain.tools import tool
import psycopg2
import os
from app.api.whatsapp import send_whatsapp_message

@tool
def alert_safety_network(user_name: str, user_lat: float, user_lon: float, radius_km: float = 1.0):
    """
    Sends actual WhatsApp alerts to nearby Safety Sisters when a worker triggers an SOS.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()

    # Query to get the phone numbers of nearby safety resources/sisters
    query = """
        SELECT name, contact_number 
        FROM spatial_resources
        WHERE type = 'Safety Sister'
        AND ST_DWithin(location, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography, %s)
        LIMIT 5;
    """
    
    try:
        cur.execute(query, (user_lon, user_lat, radius_km * 1000))
        sisters = cur.fetchall()
        
        if not sisters:
            return "No Safety Sisters found in the immediate area to notify."

        # Loop through and send the actual WhatsApp message
        alert_count = 0
        for sister_name, phone in sisters:
            alert_msg = (
                f"🚨 VESTA EMERGENCY ALERT 🚨\n\n"
                f"Our sister {user_name} is in danger nearby and has requested help. "
                f"Location: https://www.google.com/maps?q={user_lat},{user_lon}\n"
                f"Please check on her if you are nearby!"
            )
            # Uses your existing send_whatsapp_message function
            send_whatsapp_message(phone, alert_msg)
            alert_count += 1

        return f"Successfully alerted {alert_count} Safety Sisters in the area."
        
    except Exception as e:
        return f"Notification Tool Error: {str(e)}"
    finally:
        cur.close()
        conn.close()