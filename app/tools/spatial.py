# app/tools/spatial.py

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from geopy.geocoders import Nominatim
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Database Connection Logic
DB_URL = os.getenv("DATABASE_URL", "")
if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

# --- 1. HIERARCHICAL LOCATION TOOLS (New) ---

@tool
def get_districts() -> list[str]:
    """
    Fetches a list of all unique districts in West Bengal from the hierarchy table.
    Use this to show the first-level selection menu on WhatsApp.
    """
    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor() as cur:
            cur.execute("SELECT DISTINCT district FROM administrative_hierarchy ORDER BY district;")
            districts = [row[0] for row in cur.fetchall()]
            return districts
    except Exception as e:
        logger.error(f"❌ Error fetching districts: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

@tool
def get_blocks_for_district(district: str) -> list[str]:
    """
    Fetches all unique blocks within a selected district.
    Use this for the second-level selection menu.
    """
    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT block FROM administrative_hierarchy WHERE district = %s ORDER BY block;", 
                (district.upper(),)
            )
            blocks = [row[0] for row in cur.fetchall()]
            return blocks
    except Exception as e:
        logger.error(f"❌ Error fetching blocks for {district}: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

@tool
def get_villages_for_block(block: str) -> list[str]:
    """
    Fetches all unique villages within a selected block.
    Use this for the final-level selection menu.
    """
    try:
        conn = psycopg2.connect(DB_URL)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT village FROM administrative_hierarchy WHERE block = %s ORDER BY village;", 
                (block.upper(),)
            )
            villages = [row[0] for row in cur.fetchall()]
            return villages
    except Exception as e:
        logger.error(f"❌ Error fetching villages for {block}: {e}")
        return []
    finally:
        if 'conn' in locals(): conn.close()

# --- 2. GEOCODING TOOLS (Legacy / Fallback) ---

@tool
def get_lat_lon_from_name(location_name: str) -> str:
    """
    Converts a location name into latitude and longitude.
    Useful for secondary distance calculations if hierarchy is unknown.
    """
    geolocator = Nominatim(user_agent="empowernet_geocoder")
    try:
        search_query = f"{location_name}, West Bengal, India"
        location = geolocator.geocode(search_query, timeout=10)
        if location:
            logger.info(f"✅ Geocoded '{location_name}' to {location.latitude}, {location.longitude}")
            return f"{location.latitude}, {location.longitude}"
        return "None, None"
    except Exception as e:
        logger.error(f"❌ Geocoding error: {e}")
        return "None, None"

@tool
def decode_location_from_coordinates(lat: float, lon: float) -> str:
    """
    Converts GPS coordinates into a village or district name.
    """
    geolocator = Nominatim(user_agent="empowernet_geocoder")
    try:
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        if location:
            address = location.raw.get('address', {})
            place_name = address.get('village') or address.get('town') or address.get('suburb') or address.get('district')
            return place_name if place_name else "West Bengal"
        return "West Bengal"
    except Exception as e:
        logger.error(f"❌ Reverse Geocoding error: {e}")
        return "West Bengal"