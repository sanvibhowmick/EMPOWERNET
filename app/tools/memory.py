# app/tools/memory.py
import psycopg2
import psycopg2.extras
import os
from langchain_core.tools import tool

@tool
def upsert_user_profile(phone_number: str, name: str = None, language: str = None, 
                        lat: float = None, lon: float = None, skills: str = None):
    """
    Saves or updates user data. Syncs lat/lon into the PostGIS last_location field.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor()
    
    # We add a step to update the 'last_location' GEOGRAPHY point whenever lat/lon changes
    query = """
        INSERT INTO user_profiles (user_id, name, language, lat, lon, skills, last_location)
        VALUES (%s, %s, %s, %s, %s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography)
        ON CONFLICT (user_id) 
        DO UPDATE SET 
            name = COALESCE(EXCLUDED.name, user_profiles.name),
            language = COALESCE(EXCLUDED.language, user_profiles.language),
            lat = COALESCE(EXCLUDED.lat, user_profiles.lat),
            lon = COALESCE(EXCLUDED.lon, user_profiles.lon),
            skills = COALESCE(EXCLUDED.skills, user_profiles.skills),
            last_location = COALESCE(EXCLUDED.last_location, user_profiles.last_location);
    """
    try:
        # Note: ST_MakePoint takes (longitude, latitude)
        cur.execute(query, (phone_number, name, language, lat, lon, skills, lon, lat))
        conn.commit()
        return "Profile and spatial location synced."
    except Exception as e:
        return f"Database error during upsert: {e}"
    finally:
        cur.close()
        conn.close()

@tool
def get_user_context(phone_number: str):
    """
    Retrieves the user's profile. Returns coordinates and PostGIS location string.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    query = """
        SELECT name, language, skills, lat, lon, 
               ST_AsText(last_location) as location_string 
        FROM user_profiles 
        WHERE user_id = %s;
    """
    
    try:
        cur.execute(query, (phone_number,))
        result = cur.fetchone()
        if result:
            return dict(result)
        return {"error": "No profile found."}
    except Exception as e:
        return f"Database error: {e}"
    finally:
        cur.close()
        conn.close()