import streamlit as st
import re  # Importing Regex for validation
from agent import app_graph 

# --- CONFIGURATION ---
st.set_page_config(page_title="Comacks Dental Agent", page_icon="🦷", layout="centered")
st.title("Comacks Dental Automation 🦷")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "loaded" not in st.session_state:
    initial_state = {"user_message": "INIT_CHAT"}
    response = app_graph.invoke(initial_state)
    st.session_state.messages.append({"role": "assistant", "content": response['final_response']})
    st.session_state.loaded = True

# --- LOGIC ---
def process_submission(user_text):
    st.session_state.messages.append({"role": "user", "content": user_text})
    response = app_graph.invoke({"user_message": user_text})
    st.session_state.messages.append({"role": "assistant", "content": response['final_response']})

def validate_email(email):
    # Strict regex for email
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def validate_phone(phone):
    # Must be digits and at least 10 chars
    return phone.isdigit() and len(phone) >= 10

# --- RENDER LOOP ---
for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        data = msg["content"]
        
        # Simple Text
        if isinstance(data, str):
            st.write(data)
            
        # Structured UI
        elif isinstance(data, dict):
            if "text" in data: st.write(data["text"])
            if "image" in data and data["image"]: st.image(data["image"], width=300)
            
            # Buttons
            if "buttons" in data:
                cols = st.columns(len(data["buttons"]))
                for j, btn in enumerate(data["buttons"]):
                    unique_key = f"btn_{i}_{j}"
                    if cols[j].button(btn["label"], key=unique_key):
                        process_submission(btn["payload"])
                        st.rerun()

            # --- 📝 THE VALIDATED FORM ---
            if data.get("type") == "booking_form":
                # We create a unique key for the form based on the message index
                with st.form(key=f"booking_form_{i}"):
                    st.markdown("### 📋 Patient Details")
                    
                    name = st.text_input("Full Name", placeholder="John Doe")
                    phone = st.text_input("Phone Number", placeholder="9876543210")
                    email = st.text_input("Email Address", placeholder="john@gmail.com")
                    
                    submitted = st.form_submit_button("Confirm Booking")
                    
                    if submitted:
                        # --- VALIDATION LOGIC ---
                        errors = []
                        if len(name) < 2:
                            errors.append("Name is too short.")
                        if not validate_phone(phone):
                            errors.append("Phone number must be at least 10 digits.")
                        if not validate_email(email):
                            errors.append("Invalid email format (must be like name@domain.com).")
                        
                        if errors:
                            for err in errors:
                                st.error(err)
                        else:
                            # Validation Passed -> Submit to Agent
                            submission_str = f"FORM_SUBMITTED_NAME:{name}_PHONE:{phone}_EMAIL:{email}"
                            process_submission(submission_str)
                            st.rerun()

# --- MANUAL CHAT INPUT ---
if user_input := st.chat_input("Type here..."):
    process_submission(user_input)
    st.rerun()