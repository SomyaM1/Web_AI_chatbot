import os
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

# --- CONFIGURATION ---
# 🔑 ENTER YOUR GEMINI API KEY HERE (or set it in environment variables)
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSy..." # <--- PASTE YOUR KEY HERE

# Initialize Gemini (Flash is fast and good for routing)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# --- MOCK DATABASE ---
DOCTORS_DB = {
    "dr_01": {
        "id": "dr_01", 
        "name": "Dr. Sarah Jenkins", 
        "specialty": "Orthodontist", 
        "image_url": "https://img.freepik.com/free-photo/pleased-young-female-doctor-wearing-medical-robe-stethoscope-around-neck-standing-with-closed-posture_409827-254.jpg", 
        "short_bio": "Top rated Invisalign provider."
    },
    "dr_02": {
        "id": "dr_02", 
        "name": "Dr. Kenji Tanaka", 
        "specialty": "Oral Surgeon", 
        "image_url": "https://img.freepik.com/free-photo/doctor-with-his-arms-crossed-white-background_1368-5790.jpg", 
        "short_bio": "Specialist in painless extractions."
    }
}

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    user_message: str
    intent: str
    selected_doctor_id: str
    doctor_data: dict
    final_response: dict

# --- NODES (THE WORKERS) ---

def intent_classifier_node(state: AgentState):
    """
    Uses GEMINI to decide what the user wants.
    """
    msg = state.get('user_message', '').strip()
    
    # 1. Handle System Signals (Zero-Turn & Form Submissions)
    # These are hidden codes sent by UI, no need to ask LLM
    if msg == "INIT_CHAT": return {"intent": "welcome"}
    if "FORM_SUBMITTED" in msg: return {"intent": "process_booking"}
    if "ACTION_TRIGGER_BOOKING" in msg: return {"intent": "show_form"}
    if "ACTION_DETAILS" in msg:
        doc_id = msg.split("_")[-1]
        return {"intent": "doctor_details", "selected_doctor_id": doc_id}

    # 2. Use Gemini for Natural Language Understanding
    # We ask Gemini to map the user text to one of our known intents
    system_prompt = (
        "You are the brain of a dental clinic receptionist agent. "
        "Classify the User Input into exactly one of these intents: "
        "[find_doctor, services, emergency, general_chat].\n\n"
        "Rules:\n"
        "- If user asks about doctors, surgeons, dentists, or specific staff -> 'find_doctor'\n"
        "- If user asks about whitening, implants, braces, prices -> 'services'\n"
        "- If user mentions pain, blood, broken tooth, or urgent -> 'emergency'\n"
        "- Otherwise -> 'general_chat'\n\n"
        "Return ONLY the intent word."
    )
    
    try:
        response = llm.invoke(f"{system_prompt}\nUser Input: {msg}")
        intent = response.content.strip().lower()
    except Exception as e:
        print(f"LLM Error: {e}")
        intent = "general_chat" # Fallback

    return {"intent": intent}

def welcome_message_node(state: AgentState):
    return {"final_response": {
        "type": "welcome_card",
        "text": "Welcome to Comacks Dental! 🦷\nI'm your AI assistant. How can I help you today?",
        "buttons": [
            {"label": "Book Appointment", "payload": "ACTION_TRIGGER_BOOKING"},
            {"label": "Meet the Doctors", "payload": "I want to see your doctors"},
            {"label": "Our Services", "payload": "What services do you offer?"},
            {"label": "Emergency", "payload": "I have an emergency"}
        ]
    }}

def retrieve_doctor_profile_node(state: AgentState):
    # We can also use Gemini here to extract "Surgeon" vs "Orthodontist" if we wanted
    # For now, simple keyword check is faster for the demo DB
    msg = state.get('user_message', '').lower()
    
    if "surgeon" in msg or "implant" in msg or "extraction" in msg:
        doc = DOCTORS_DB["dr_02"]
    else:
        doc = DOCTORS_DB["dr_01"]
        
    return {"doctor_data": doc, "selected_doctor_id": doc["id"], "final_response": {
        "type": "card",
        "text": f"Based on your request, I highly recommend **{doc['name']}**.",
        "image": doc["image_url"],
        "buttons": [
            {"label": "More Info", "payload": f"ACTION_DETAILS_{doc['id']}"},
            {"label": "Book Now", "payload": "ACTION_TRIGGER_BOOKING"}
        ]
    }}

def retrieve_doctor_details_node(state: AgentState):
    doc_id = state.get('selected_doctor_id', 'dr_01')
    doc = DOCTORS_DB.get(doc_id, DOCTORS_DB['dr_01'])
    return {"final_response": {
        "type": "card", 
        "text": f"**{doc['name']}**\n{doc['short_bio']}\n\nAvailability: Mon-Fri (9am - 5pm)",
        "buttons": [{"label": "Book This Doctor", "payload": "ACTION_TRIGGER_BOOKING"}]
    }}

def show_booking_form_node(state: AgentState):
    return {"final_response": {
        "type": "booking_form",
        "text": "Please enter your details to schedule your visit."
    }}

def process_booking_node(state: AgentState):
    # The UI sends data like: "FORM_SUBMITTED_NAME:John_PHONE:123..."
    # Here we just confirm receipt. In a real app, you'd parse this string and save to SQL.
    return {"final_response": {
        "type": "text",
        "text": "✅ **Success!**\n\nYour appointment request has been received. Our coordinator will contact you shortly to confirm the exact time."
    }}

def general_chat_node(state: AgentState):
    # We can let Gemini answer general questions too
    msg = state.get('user_message', '')
    response = llm.invoke(f"You are a helpful dental assistant. Answer this patient briefly: {msg}")
    
    return {"final_response": {
        "type": "text", 
        "text": response.content
    }}

def service_info_node(state: AgentState):
    return {"final_response": {
        "type": "text",
        "text": "We offer:\n- ✨ Teeth Whitening\n- 🦷 Dental Implants\n- 😬 Invisalign\n- 🛡️ General Checkups",
        "buttons": [{"label": "Book Service", "payload": "ACTION_TRIGGER_BOOKING"}]
    }}

def emergency_node(state: AgentState):
    return {"final_response": {
        "type": "text",
        "text": "🚨 **Emergency Protocol**\nIf you are in severe pain or bleeding, please call our 24/7 hotline immediately: **555-0199**.\n\nFor urgent but non-life-threatening issues, book a slot below.",
        "buttons": [{"label": "Book Urgent Slot", "payload": "ACTION_TRIGGER_BOOKING"}]
    }}

# --- GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)

# Register Nodes
workflow.add_node("classifier", intent_classifier_node)
workflow.add_node("welcome", welcome_message_node)
workflow.add_node("find_doctor", retrieve_doctor_profile_node)
workflow.add_node("doctor_details", retrieve_doctor_details_node)
workflow.add_node("show_form", show_booking_form_node)
workflow.add_node("process_booking", process_booking_node)
workflow.add_node("services", service_info_node)
workflow.add_node("emergency", emergency_node)
workflow.add_node("general", general_chat_node)

# Router Logic
def router(state):
    # Maps the intent string to the node name
    intent_map = {
        "welcome": "welcome",
        "find_doctor": "find_doctor",
        "doctor_details": "doctor_details",
        "show_form": "show_form",
        "process_booking": "process_booking",
        "services": "services",
        "emergency": "emergency",
        "general_chat": "general"
    }
    return intent_map.get(state["intent"], "general")

workflow.set_entry_point("classifier")
workflow.add_conditional_edges("classifier", router)

# All nodes go to END (Single turn interaction)
for node in ["welcome", "find_doctor", "doctor_details", "show_form", "process_booking", "services", "emergency", "general"]:
    workflow.add_edge(node, END)

app_graph = workflow.compile()