# app/tools/spatial.py

import logging
from typing import Optional, Tuple
from sqlalchemy import text
from geopy.geocoders import Nominatim
from langchain_core.tools import tool

from app.core.db import engine

logger = logging.getLogger(__name__)

# --- 1. HIERARCHICAL LOCATION TOOLS ---


@tool
def get_districts() -> list[str]:
    """
    Fetches a list of all unique districts in West Bengal from the hierarchy table.
    Use this to show the first-level selection menu on WhatsApp.
    """
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT DISTINCT district FROM administrative_hierarchy ORDER BY district;")
            ).fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"❌ Error fetching districts: {e}")
        return []

@tool
def get_blocks_for_district(district: str) -> list[str]:
    """
    Fetches all unique blocks within a selected district.
    Use this for the second-level selection menu.
    """
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT DISTINCT block FROM administrative_hierarchy WHERE district = :district ORDER BY block;"),
                {"district": district.upper()},
            ).fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"❌ Error fetching blocks for {district}: {e}")
        return []

@tool
def get_villages_for_block(block: str) -> list[str]:
    """
    Fetches all unique villages within a selected block.
    Use this for the final-level selection menu.
    """
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text("SELECT DISTINCT village FROM administrative_hierarchy WHERE block = :block ORDER BY village;"),
                {"block": block.upper()},
            ).fetchall()
            return [row[0] for row in rows]
    except Exception as e:
        logger.error(f"❌ Error fetching villages for {block}: {e}")
        return []


@tool
def get_village_coordinates(district: str, block: str, village: str) -> Optional[Tuple[float, float]]:
    """
    Looks up the (lat, lon) centroid of a specific village from
    administrative_hierarchy.village_center_geog.


    """
    try:
        with engine.connect() as conn:
            row = conn.execute(
                text(
                    """
                    SELECT ST_Y(village_center_geog::geometry) AS lat,
                           ST_X(village_center_geog::geometry) AS lon
                    FROM administrative_hierarchy
                    WHERE district = :district AND block = :block AND village = :village
                      AND village_center_geog IS NOT NULL
                    LIMIT 1;
                    """
                ),
                {"district": district.upper(), "block": block.upper(), "village": village.upper()},
            ).fetchone()
            if row and row[0] is not None and row[1] is not None:
                return (float(row[0]), float(row[1]))
            return None
    except Exception as e:
        logger.error(f"❌ Error fetching coordinates for {village}, {block}: {e}")
        return None



@tool
def get_lat_lon_from_name(location_name: str) -> str:
    """
    Converts a location name into latitude and longitude.
    Reserved for a future free-text location fallback (not currently wired
    into the graph -- see module docstring). Useful for secondary distance
    calculations if hierarchy is unknown.
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
    Called from app/api/whatsapp.py when a user shares a WhatsApp location pin.
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
