import streamlit as st
import qrcode
from io import BytesIO

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart Restaurant Voice Menu",
    page_icon="🍽️",
    layout="centered"
)

# --- 1. Handle Table ID from URL Query Parameters ---
# Streamlit's st.query_params reads parameters from the URL (e.g., ?table_id=1)
query_params = st.query_params
table_id = query_params.get("table_id", "1")  # Default to Table 1 if not specified

# --- 2. Restaurant Menu Database ---
MENU = {
    "Starters": {
        "Garlic Bread": 5.99,
        "Bruschetta": 6.50,
        "Chicken Wings": 8.99,
        "Paneer Tikka": 7.99
    },
    "Main Course": {
        "Margherita Pizza": 12.99,
        "Pepperoni Pizza": 14.99,
        "Creamy Alfredo Pasta": 13.50,
        "Grilled Chicken Steak": 16.00,
        "Veggie Burger": 10.99
    },
    "Beverages": {
        "Coca Cola": 2.50,
        "Iced Lemon Tea": 3.00,
        "Fresh Lime Soda": 2.80,
        "Chocolate Milkshake": 4.50
    }
}

# --- UI Header ---
st.title("🍽️ Digital Voice-Enabled Menu")
st.markdown(f"### 📍 Ordering for: **Table {table_id}**")
st.write("Browse our menu below or use the voice assistant to place your order!")

# --- 3. Sections to Toggle Between Categories ---
category = st.radio(
    "Select Menu Category", 
    options=["Starters", "Main Course", "Beverages"], 
    horizontal=True
)

st.divider()

# --- Display Items for Selected Category ---
st.subheader(f"📋 {category} Menu")
selected_category_items = MENU[category]

for item_name, price in selected_category_items.items():
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"**{item_name}**")
    with col2:
        st.markdown(f"${price:.2f}")
    with col3:
        if st.button("Add", key=f"add_{item_name}"):
            st.toast(f"Added {item_name} to cart!", icon="✅")

# --- 4. Sidebar: QR Code Generator for Table 1 (and others) ---
st.sidebar.header("🛠️ Admin / Table Setup")
st.sidebar.write("Generate QR codes for physical tables.")

# Input box to generate QR for any table ID
input_table_id = st.sidebar.text_input("Enter Table ID for QR", value=str(table_id))

# Assuming localhost for testing, change to your deployed Vercel/Streamlit Community URL later
base_url = "https://your-streamlit-app-url.streamlit.app" 
target_url = f"{base_url}/?table_id={input_table_id}"

st.sidebar.text_input("Generated QR Link:", value=target_url)

# Generate QR Code image
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(target_url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")

# Convert PIL image to byte buffer for Streamlit display
buf = BytesIO()
img.save(buf, format="PNG")
byte_im = buf.getvalue()

st.sidebar.image(byte_im, caption=f"Scan to open Table {input_table_id} Menu", use_container_width=True)
