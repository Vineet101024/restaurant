import os
import json
from google import genai
from google.genai import types
from supabase import create_client
from menu import MENU_DATA

# --- Initialize Free Gemini Client ---
# Set GEMINI_API_KEY in your Streamlit secrets or environment variables
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or st_api_key_helper()
    return genai.Client(api_key=api_key)

def st_api_key_helper():
    import streamlit as st
    return st.secrets.get("GEMINI_API_KEY", "")

# --- Initialize Supabase Client ---
def get_supabase_client():
    import streamlit as st
    url = st.secrets.get("SUPABASE_URL", "YOUR_SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY", "YOUR_SUPABASE_KEY")
    return create_client(url, key)





def save_order_to_db(table_id: str, order_items: list) -> str:
    """Saves the pending order to Supabase and returns the order ID."""
    supabase = get_supabase_client()
    total_price = sum(
        MENU_DATA[cat][item] * qty 
        for cat in MENU_DATA 
        for item, qty in [(oi["item"], oi["quantity"]) for oi in order_items if oi["item"] in MENU_DATA[cat]]
    )
    
    data = {
        "table_id": str(table_id),
        "items": order_items,
        "total_price": total_price,
        "status": "pending"
    }
    
    response = supabase.table("orders").insert(data).execute()
    if response.data:
        return response.data[0].get("id", "1")
    return "1"


def check_order_status(order_id: str) -> str:
    """Fetches current order status from Supabase."""
    if not order_id:
        return "pending"
    supabase = get_supabase_client()
    res = supabase.table("orders").select("status").eq("id", order_id).execute()
    if res.data:
        return res.data[0].get("status", "pending")
    return "pending"


def generate_whatsapp_url(restaurant_phone: str, table_id: str, order_items: list, order_id: str) -> str:
    """Generates a Click-to-Chat WhatsApp URL for the restaurant owner."""
    items_str = "\n".join([f"- {oi['quantity']}x {oi['item']}" for oi in order_items])
    message = f"🔔 *New Order Received!*\n\n📍 *Table:* {table_id}\n🆔 *Order ID:* {order_id}\n\n{items_str}\n\nReply 'Yes' or approve this order."
    import urllib.parse
    encoded_msg = urllib.parse.quote(message)
    return f"https://wa.me/{restaurant_phone}?text={encoded_msg}"

def parse_voice_order(spoken_text: str) -> list:
    """Uses Gemini Free tier to extract menu items and quantities from speech text flexibly."""
    try:
        client = get_gemini_client()
        
        # Build menu reference list
        flat_menu = []
        for cat, items in MENU_DATA.items():
            for item in items.keys():
                flat_menu.append(item)

        prompt = f""" You are a smart restaurant order assistant. Your job is to extract menu items and quantities from the user's conversational speech.
        
        Available Exact Menu Items: {flat_menu}
        
        User Spoken Order: "{spoken_text}"
        
        Instructions:
        1. Match what the user said to the closest Available Exact Menu Items (ignore case differences like "coke" vs "Coca Cola").
        2. If no quantity is specified, assume quantity is 1.
        3. Return ONLY a valid JSON list of objects with keys "item" (exact string from the menu list) and "quantity" (integer).
        4. If nothing matches, return []. Do not include markdown codeblocks or extra text.
        
        Example format:
        [ {{"item": "Garlic Bread", "quantity": 1}}, {{"item": "Paneer Tikka", "quantity": 1}} ]
        
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_text)
    except Exception as e:
        print(f"Error parsing order: {e}")
        return []
