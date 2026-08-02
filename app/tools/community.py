# app/tools/community.py

import logging
from sqlalchemy import text
from langchain_core.tools import tool

from app.core.db import engine

logger = logging.getLogger(__name__)

@tool("find_nearby_shgs")
def find_nearby_shgs(district: str, block: str, village: str):
    """
    Locates Self-Help Groups (SHGs) and community circles near the user.
    Priority 1: Groups in the same Village.
    Priority 2: Groups in the same Block.
    Priority 3: Groups in the same District.
    """

    query = text("""
        SELECT
            shg_name,
            leader_name,
            contact_number,
            district,
            block,
            gram_panchayat,
            village,
            category,
            formation_date,
            nrlm_shg_id
        FROM self_help_groups
        WHERE
            village  = :village
            OR block = :block
            OR district = :district
        ORDER BY
            (CASE
                WHEN village  = :village THEN 1
                WHEN block    = :block THEN 2
                WHEN district = :district THEN 3
                ELSE 4
            END) ASC,
            shg_name ASC
        LIMIT 10;
    """)

    try:
        with engine.connect() as conn:
            res = conn.execute(query, {"village": village, "block": block, "district": district}).fetchall()

            if not res:
                return (
                    f"I couldn't find any registered SHGs in "
                    f"{village} or {block} yet. Try checking with your local Panchayat."
                )

            results = []
            for r in res:
                if r.village == village:
                    match_level = "Immediate Village"
                elif r.block == block:
                    match_level = "Nearby in Block"
                else:
                    match_level = "District Level"

                loc_parts = [p for p in [r.village, r.gram_panchayat, r.block] if p]
                results.append({
                    "name":        r.shg_name,
                    "leader":      r.leader_name or "Not Listed",
                    "contact":     r.contact_number or "N/A",
                    "location":    ", ".join(loc_parts) or r.district,
                    "category":    r.category or "General",
                    "formed":      str(r.formation_date) if r.formation_date else "N/A",
                    "nrlm_id":     r.nrlm_shg_id or "N/A",
                    "match_level": match_level,
                })

            return results

    except Exception as e:
        logger.error(f"❌ Community Tool Error: {e}")
        return f"Error searching for community groups in {block}."
