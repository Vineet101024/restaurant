import streamlit as st
import qrcode
from io import BytesIO
from streamlit_mic_recorder import speech_to_text
from menu import MENU_DATA
from services import parse_voice_order, save_order_to_db, check_order_status, generate_whatsapp_url

# Page Configuration
st.set_page_config(page_title="Voice Restaurant Menu", page_icon="🎙️", layout="centered")

# Retrieve URL query parameters for Table ID
query_params = st.query_params
table_id = query_params.get("table_id", "1")

# Initialize Session State
if "cart" not in st.session_state:
    st.session_state.cart = []
if "order_id" not in st.session_state:
    st.session_state.order_id = None
if "order_placed" not in st.session_state:
    st.session_state.order_placed = False

st.title("🍽️ Smart Voice Restaurant")
st.markdown(f"### 📍 Ordering from: **Table {table_id}**")

# Check if order was already placed and look up approval status
if st.session_state.order_placed and st.session_state.order_id:
    current_status = check_order_status(st.session_state.order_id)
    if current_status == "approved" or current_status == "yes":
        st.success("🎉 Your order has been approved by the restaurant owner and is being prepared!")
        if st.button("Place New Order"):
            st.session_state.cart = []
            st.session_state.order_id = None
            st.session_state.order_placed = False
            st.rerun()
        st.stop()
    else:
        st.info("⏳ Order sent to restaurant owner via WhatsApp. Waiting for approval...")
        if st.button("Refresh Status"):
            st.rerun()
        st.stop()

# --- Voice Order Section ---
st.subheader("🎙️ Voice Assistant")
st.write("Click the microphone button and speak your order (e.g., *'I want two margherita pizzas and one coke'*):")

spoken_text = speech_to_text(language='en', start_prompt="🗣️ Speak Order", stop_prompt="🛑 Stop Recording", key='voice_input')

if spoken_text:
    st.info(f"You said: *\"{spoken_text}\"*")
    extracted_items = parse_voice_order(spoken_text)
    if extracted_items:
        st.session_state.cart = extracted_items
        st.success("Items successfully extracted from voice!")
    else:
        st.warning("Could not match speech to any menu items. Please try again.")

st.divider()

# --- Interactive Category Tabs ---
category = st.radio("Menu Categories", options=list(MENU_DATA.keys()), horizontal=True)
st.subheader(f"📋 {category}")

for item_name, price in MENU_DATA[category].items():
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown(f"**{item_name}**")
    with col2:
        st.markdown(f"${price:.2f}")
    with col3:
        if st.button("Add", key=f"btn_{item_name}"):
            # Add or increment item in cart
            existing = next((x for x in st.session_state.cart if x["item"] == item_name), None)
            if existing:
                existing["quantity"] += 1
            else:
                st.session_state.cart.append({"item": item_name, "quantity": 1})
            st.toast(f"Added {item_name}", icon="✅")

st.divider()

# --- Order Cart & Review Summary ---
st.subheader("🛒 Current Order Summary")

if not st.session_state.cart:
    st.info("Your cart is empty. Speak your order or click 'Add' on items above.")
else:
    total = 0
    for idx, cart_item in enumerate(st.session_state.cart):
        item_name = cart_item["item"]
        qty = cart_item["quantity"]
        # Find price across categories
        price = next((MENU_DATA[cat][item_name] for cat in MENU_DATA if item_name in MENU_DATA[cat]), 0)
        item_total = price * qty
        total += item_total
        
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"**{item_name}**")
        with col2:
            st.write(f"Qty: {qty}")
        with col3:
            st.write(f"${item_total:.2f}")

    st.markdown(f"### Total Amount: **${total:.2f}**")
    
    col_confirm, col_reject = st.columns(2)
    
    with col_reject:
        if st.button("❌ Reject / Clear", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
            
    with col_confirm:
        if st.button("✅ Confirm Order", type="primary", use_container_width=True):
            # 1. Save to database
            new_id = save_order_to_db(table_id, st.session_state.cart)
            st.session_state.order_id = new_id
            st.session_state.order_placed = True
            
            # 2. Build WhatsApp redirect URL for the owner (replace with actual restaurant phone number e.g. 15551234567)
            restaurant_whatsapp = "9425391363" 
            wa_url = generate_whatsapp_url(restaurant_whatsapp, table_id, st.session_state.cart, new_id)
            
            st.success("Order saved to database!")
            st.markdown(f"👉 **[Click here to send order to Restaurant Owner via WhatsApp]({wa_url})**")
            st.rerun()

# --- Sidebar: Table QR Code Generator ---
st.sidebar.header("🛠️ Admin Tools")
input_table = st.sidebar.text_input("Generate QR for Table ID", value=str(table_id))
app_url = f"https://restaurant-sheopur.streamlit.app/?table_id={input_table}"

st.sidebar.text_input("Table Link:", value=app_url)
qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(app_url)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")

buf = BytesIO()
img.save(buf, format="PNG")
st.sidebar.image(buf.getvalue(), caption=f"Scan for Table {input_table}", use_container_width=True)
