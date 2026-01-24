from langchain.tools import tool
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

@tool
def get_user_context(phone_number: str):
    """
    Retrieves the worker's permanent profile, including name, language, 
    and village. Use this at the start of a conversation to personalize help.
    """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    query = "SELECT name, language FROM user_profiles WHERE user_id = %s"
    
    try:
        cur.execute(query, (phone_number,))
        result = cur.fetchone()
        if result:
            return f"User Name: {result[0]}, Preferred Language: {result[1]}"
        return "New user. No profile found yet."
    finally:
        cur.close()
        conn.close()

@tool
def update_worker_profile(phone_number: str, key: str, value: str):
    """
    Updates a specific piece of information about the worker in the database.
    Example: key='name', value='Sunita' or key='language', value='Bengali'.
    """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    
    # Dynamic update query based on the key provided
    query = f"UPDATE user_profiles SET {key} = %s WHERE user_id = %s"
    
    try:
        cur.execute(query, (value, phone_number))
        conn.commit()
        return f"Successfully updated {key} to {value}."
    except Exception as e:
        return f"Error updating profile: {str(e)}"
    finally:
        cur.close()
        conn.close()