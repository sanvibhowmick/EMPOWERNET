import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Handle Neon/Postgres URL naming
DB_URL = os.getenv("DATABASE_URL", "")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

def upsert_user_profile(
    phone_number: str, 
    name: str = None, 
    language: str = None, 
    district: str = None, 
    block: str = None, 
    village: str = None, 
    occupation: str = None, 
    skill_level: str = None
):
    """
    Saves or updates the user's profile in the database.
    Removed lat/lon to match the new hierarchical schema.
    """
    sql = """
        INSERT INTO user_profile (
            phone_number, full_name, preferred_lang, district, block, 
            village, primary_occupation, skill_level
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (phone_number) DO UPDATE SET
            full_name = COALESCE(EXCLUDED.full_name, user_profile.full_name),
            preferred_lang = COALESCE(EXCLUDED.preferred_lang, user_profile.preferred_lang),
            district = COALESCE(EXCLUDED.district, user_profile.district),
            block = COALESCE(EXCLUDED.block, user_profile.block),
            village = COALESCE(EXCLUDED.village, user_profile.village),
            primary_occupation = COALESCE(EXCLUDED.primary_occupation, user_profile.primary_occupation),
            skill_level = COALESCE(EXCLUDED.skill_level, user_profile.skill_level);
    """
    
    try:
        conn = psycopg2.connect(DB_URL)
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    phone_number, name, language, district, block, 
                    village, occupation, skill_level
                ))
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database Upsert Error: {e}")
        return False

def get_user_context(phone_number: str):
    """
    Retrieves the existing profile to prime the AgentState.
    """
    sql = """
        SELECT full_name, preferred_lang, district, block, village, 
               primary_occupation, skill_level 
        FROM user_profile 
        WHERE phone_number = %s
    """
    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (phone_number,))
            res = cur.fetchone()
            if res:
                return dict(res)
            return None
    except Exception as e:
        logger.error(f"❌ Database Retrieval Error: {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()