# app/tools/reporting.py

import logging
from typing import Optional
from langchain_core.tools import tool
from sqlalchemy import text

from app.core.db import engine

logger = logging.getLogger(__name__)

@tool("submit_safety_report")
def submit_safety_report(
    user_id: str,
    description: str,
    category: str,
    district: str,
    block: str,
    village: str,
    lat: Optional[float] = None,
    lon: Optional[float] = None,
):
    """
    Logs a safety complaint in English and automatically updates the safety score
    of all vetted job sites in the reporter's specific village.

    FIX (weak point #12): lat/lon are now accepted and stored (best-effort --
    they may be None if no coordinates were resolvable for the village).
    Previously this always left lat/lon NULL, which meant every report filed
    through the real WhatsApp bot was invisible to the NGO dashboard's
    lat/lon-bounding-box safety queries. reporting_node resolves these via
    app/tools/spatial.py's get_village_coordinates before calling this tool.
    """

    # 1. SQL to insert the report using Hierarchy + (optional) coordinates
    insert_query = text("""
        INSERT INTO safety_reports (user_id, description, category, district, block, village, lat, lon, reported_at)
        VALUES (:uid, :desc, :cat, :dist, :block, :vill, :lat, :lon, CURRENT_TIMESTAMP)
        RETURNING id;
    """)

    # 2. SQL to penalize job sites in the same Village/Block
    # This ensures the Swarm penalizes the right local area without needing GPS.
    update_score_query = text("""
        UPDATE vetted_jobs
        SET safety_score = GREATEST(1.0, safety_score - 0.5)
        WHERE village = :vill AND block = :block;
    """)

    try:
        with engine.begin() as conn:
            # Execute the insert
            result = conn.execute(insert_query, {
                "uid": user_id,
                "desc": description,
                "cat": category,
                "dist": district,
                "block": block,
                "vill": village,
                "lat": lat,
                "lon": lon,
            })
            report_id = result.fetchone()[0]

            # Execute the score update for that specific village/block
            update_result = conn.execute(update_score_query, {
                "vill": village,
                "block": block,
            })
            affected_sites = update_result.rowcount

            logger.info(f"🚩 Safety Report #{report_id} logged. {affected_sites} sites in {village} penalized.")

            return {
                "status": "success",
                "report_id": report_id,
                "sites_impacted": affected_sites,
                "message": f"Report filed for {village}. Safety scores for {affected_sites} local sites adjusted.",
            }

    except Exception as e:
        logger.error(f"❌ Reporting Tool Failure: {e}")
        return {
            "status": "error",
            "message": f"Database transaction failed: {str(e)}",
        }
