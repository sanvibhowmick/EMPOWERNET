# app/tools/memory.py

import logging
from sqlalchemy import text

from app.core.db import engine

logger = logging.getLogger(__name__)



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
    """
    sql = text("""
        INSERT INTO user_profile (
            phone_number, full_name, preferred_lang, district, block,
            village, primary_occupation, skill_level
        )
        VALUES (:phone_number, :name, :language, :district, :block,
                :village, :occupation, :skill_level)
        ON CONFLICT (phone_number) DO UPDATE SET
            full_name = COALESCE(EXCLUDED.full_name, user_profile.full_name),
            preferred_lang = COALESCE(EXCLUDED.preferred_lang, user_profile.preferred_lang),
            district = COALESCE(EXCLUDED.district, user_profile.district),
            block = COALESCE(EXCLUDED.block, user_profile.block),
            village = COALESCE(EXCLUDED.village, user_profile.village),
            primary_occupation = COALESCE(EXCLUDED.primary_occupation, user_profile.primary_occupation),
            skill_level = COALESCE(EXCLUDED.skill_level, user_profile.skill_level);
    """)

    try:
        with engine.begin() as conn:
            conn.execute(sql, {
                "phone_number": phone_number, "name": name, "language": language,
                "district": district, "block": block, "village": village,
                "occupation": occupation, "skill_level": skill_level,
            })
        return True
    except Exception as e:
        logger.error(f"❌ Database Upsert Error: {e}")
        return False


def get_user_context(phone_number: str):
    """
    Retrieves the existing profile to prime the AgentState.
    """
    sql = text("""
        SELECT full_name, preferred_lang, district, block, village,
               primary_occupation, skill_level
        FROM user_profile
        WHERE phone_number = :phone_number
    """)
    try:
        with engine.connect() as conn:
            row = conn.execute(sql, {"phone_number": phone_number}).mappings().fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"❌ Database Retrieval Error: {e}")
        return None
