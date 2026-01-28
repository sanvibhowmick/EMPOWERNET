import os
import logging
from typing import List, Optional
from langchain_core.tools import tool
from sqlalchemy import create_engine, text
from pydantic import BaseModel, Field

# Set up logging for the tool
logger = logging.getLogger(__name__)

# 1. DATABASE CONNECTION
# Uses your NeonDB URL from environment variables
DB_URL = os.getenv("NEON_DATABASE_URL")
engine = create_engine(DB_URL)

# 2. SCHEMA DEFINITION
# This schema ensures Pydantic validates the inputs from Sangini Node
class JobSearchInput(BaseModel):
    user_skills: List[str] = Field(description="List of skills/interests to match with job titles")
    user_lat: Optional[float] = Field(default=None, description="User's latitude (from GPS pin)")
    user_lon: Optional[float] = Field(default=None, description="User's longitude (from GPS pin)")
    location_name: Optional[str] = Field(default=None, description="Village or town name to search if GPS is missing")

@tool("match_skills_to_jobs", args_schema=JobSearchInput)
def match_skills_to_jobs(
    user_skills: List[str], 
    user_lat: Optional[float] = None, 
    user_lon: Optional[float] = None,
    location_name: Optional[str] = None
) -> str:
    """
    Search for vetted jobs in the database. 
    Matches by skills and uses a 10km PostGIS radius or a village name fallback.
    """
    
    # 3. DUAL-LOGIC SQL QUERY
    # Combines geographic proximity and string matching for maximum flexibility
    query = text("""
        SELECT title, employer_name, daily_wage, village_name, contact_info
        FROM vetted_jobs
        WHERE (
            -- Priority 1: Geographic match (within 10km)
            (:lat IS NOT NULL AND :lon IS NOT NULL AND 
             ST_DWithin(location, ST_MakePoint(:lon, :lat)::geography, 10000))
            OR
            -- Priority 2: Text match on village name
            (:loc_name IS NOT NULL AND LOWER(village_name) LIKE LOWER(:loc_name_pattern))
        )
        AND (
            -- Skill filter (matches any provided skill against the title)
            title ILIKE ANY(:skills)
        )
        LIMIT 3;
    """)

    # Prepare patterns for SQL execution
    skills_patterns = [f"%{s}%" for s in user_skills]
    loc_pattern = f"%{location_name}%" if location_name else None

    try:
        with engine.connect() as conn:
            result = conn.execute(query, {
                "lat": user_lat,
                "lon": user_lon,
                "loc_name": location_name,
                "loc_name_pattern": loc_pattern,
                "skills": skills_patterns
            })
            
            rows = result.fetchall()
            
            if not rows:
                return "I couldn't find any matching jobs nearby. Try searching in a different village name."

            # 4. OUTPUT FORMATTING
            # Returns raw text for the Sangini node to process
            job_list = []
            for row in rows:
                job_list.append(
                    f"📍 {row.title} at {row.employer_name}\n"
                    f"   Wage: ₹{row.daily_wage}/day\n"
                    f"   Location: {row.village_name}\n"
                    f"   Contact: {row.contact_info}"
                )
            
            return "\n\n".join(job_list)

    except Exception as e:
        logger.error(f"❌ Database error in jobs.py: {e}")
        return f"Database error: {str(e)}"