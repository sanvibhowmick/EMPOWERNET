import os
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Handle Neon/Postgres URL naming
raw_url = os.getenv("DATABASE_URL", "")
if raw_url.startswith("postgres://"):
    raw_url = raw_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(raw_url)

def upsert_user_profile(phone_number: str, name: str = None, language: str = None, skills: str = None, lat: float = None, lon: float = None):
    """
    Saves or updates the user's profile in the database.
    """
    query = text("""
        INSERT INTO user_profiles (phone_number, name, preferred_lang, skills, lat, lon, last_seen)
        VALUES (:phone, :name, :lang, :skills, :lat, :lon, CURRENT_TIMESTAMP)
        ON CONFLICT (phone_number) DO UPDATE SET
            name = COALESCE(EXCLUDED.name, user_profiles.name),
            preferred_lang = COALESCE(EXCLUDED.preferred_lang, user_profiles.preferred_lang),
            skills = COALESCE(EXCLUDED.skills, user_profiles.skills),
            lat = COALESCE(EXCLUDED.lat, user_profiles.lat),
            lon = COALESCE(EXCLUDED.lon, user_profiles.lon),
            last_seen = CURRENT_TIMESTAMP;
    """)
    
    try:
        with engine.connect() as conn:
            conn.execute(query, {
                "phone": phone_number, "name": name, "lang": language, 
                "skills": skills, "lat": lat, "lon": lon
            })
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Database Upsert Error: {e}")
        return False

def get_user_context(phone_number: str):
    """
    Retrieves the existing profile to prime the AgentState.
    """
    query = text("SELECT name, preferred_lang, skills, lat, lon FROM user_profiles WHERE phone_number = :phone")
    try:
        with engine.connect() as conn:
            res = conn.execute(query, {"phone": phone_number}).fetchone()
            if res:
                return {
                    "name": res[0], "preferred_lang": res[1], 
                    "skills": res[2], "lat": res[3], "lon": res[4]
                }
            return None
    except Exception as e:
        logger.error(f"❌ Database Retrieval Error: {e}")
        return None