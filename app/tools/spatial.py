from langchain_core.tools import tool
import os
import psycopg2
import logging
from geopy.geocoders import Nominatim
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
logger = logging.getLogger(__name__)

@tool
def get_lat_lon_from_name(location_name: str) -> str:
    """
    Converts a location name (village, town, or district) into latitude and longitude.
    Returns the coordinates as a string "lat, lon".
    """
    geolocator = Nominatim(user_agent="empowernet_geocoder")
    try:
        search_query = f"{location_name}, West Bengal, India"
        location = geolocator.geocode(search_query, timeout=10)
        if location:
            logger.info(f"✅ Geocoded '{location_name}' to {location.latitude}, {location.longitude}")
            return f"{location.latitude}, {location.longitude}"
        return f"None, None"
    except Exception as e:
        logger.error(f"❌ Geocoding error: {e}")
        return "None, None"

@tool
def decode_location_from_coordinates(lat: float, lon: float) -> str:
    """
    Converts GPS coordinates into a human-readable village or district name.
    Use this when you have lat/lon but need the place name for the final response.
    """
    geolocator = Nominatim(user_agent="empowernet_geocoder")
    try:
        # Reverse geocoding
        location = geolocator.reverse(f"{lat}, {lon}", timeout=10)
        if location:
            # We extract the village/town or suburb for a localized feel
            address = location.raw.get('address', {})
            place_name = address.get('village') or address.get('town') or address.get('suburb') or address.get('district')
            return place_name if place_name else "West Bengal"
        return "West Bengal"
    except Exception as e:
        logger.error(f"❌ Reverse Geocoding error: {e}")
        return "West Bengal"
