import os
from typing import TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

# --- CONFIGURATION ---
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyB-jse114KOGmSoKw7N7VS9KKXtkqDz228" # <--- PASTE KEY HERE

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# --- MOCK DATABASE ---
DOCTORS_DB = {
    "dr_01": {
        "id": "dr_01", "name": "Dr. Sarah Jenkins", "specialty": "Orthodontist", 
        "image_url": "https://img.freepik.com/free-photo/pleased-young-female-doctor-wearing-medical-robe-stethoscope-around-neck-standing-with-closed-posture_409827-254.jpg", 
        "short_bio": "Top rated Invisalign provider."
    },
    "dr_02": {
        "id": "dr_02", "name": "Dr. Kenji Tanaka", "specialty": "Oral Surgeon", 
        "image_url": "https://img.freepik.com/free-photo/doctor-with-his-arms-crossed-white-background_1368-5790.jpg", 
        "short_bio": "Specialist in painless extractions."
    }
}

# --- STATE DEFINITION ---
class AgentState(TypedDict):
    user_message: str
    chat_history: List[str]     # <--- NEW: Holds the memory
    intent: str
    selected_doctor_id: str
    doctor_data: dict
    final_response: dict

# --- NODES ---

def intent_classifier_node(state: AgentState):
    msg = state.get('user_message', '').strip()
    history = "\n".join(state.get('chat_history', [])[-5:]) # Look at last 5 turns
    
    if msg == "INIT_CHAT": return {"intent": "welcome"}
    if "FORM_SUBMITTED" in msg: return {"intent": "process_booking"}
    if "ACTION_TRIGGER_BOOKING" in msg: return {"intent": "show_form"}
    if "ACTION_DETAILS" in msg:
        doc_id = msg.split("_")[-1]
        return {"intent": "doctor_details", "selected_doctor_id": doc_id}

    # Classify with Context
    system_prompt = (
        "Classify intent: [find_doctor, services, emergency, general_chat].\n"
        "Context:\n" + history + "\n"
        "Rules:\n"
        "- Ask for doctor/surgeon/staff -> 'find_doctor'\n"
        "- Whitening/implants/price -> 'services'\n"
        "- Pain/blood/urgent -> 'emergency'\n"
        "- Otherwise -> 'general_chat'\n"
        "Return ONLY the intent word."
    )
    
    try:
        response = llm.invoke(f"{system_prompt}\nUser Input: {msg}")
        intent = response.content.strip().lower()
    except:
        intent = "general_chat"

    return {"intent": intent}

def general_chat_node(state: AgentState):
    msg = state.get('user_message', '')
    history = "\n".join(state.get('chat_history', []))
    
    # Prompt with Memory
    prompt = (
        "You are a helpful dental assistant at Comacks Dental.\n"
        "Use the chat history to answer contextually.\n"
        f"Chat History:\n{history}\n"
        f"Patient: {msg}\n"
        "Answer briefly and professionally."
    )
    
    response = llm.invoke(prompt)
    
    return {"final_response": {
        "type": "text", 
        "text": response.content
    }}

# --- STANDARD NODES (Unchanged Logic) ---
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
    msg = state.get('user_message', '').lower()
    if "surgeon" in msg or "implant" in msg: doc = DOCTORS_DB["dr_02"]
    else: doc = DOCTORS_DB["dr_01"]
    return {"doctor_data": doc, "selected_doctor_id": doc["id"], "final_response": {
        "type": "card",
        "text": f"I recommend *{doc['name']}*.",
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
        "text": f"*{doc['name']}*\n{doc['short_bio']}\nAvailability: Mon-Fri",
        "buttons": [{"label": "Book This Doctor", "payload": "ACTION_TRIGGER_BOOKING"}]
    }}

def show_booking_form_node(state: AgentState):
    return {"final_response": {"type": "booking_form", "text": "Please enter your details."}}

def process_booking_node(state: AgentState):
    return {"final_response": {"type": "text", "text": "✅ *Success!* Appointment received."}}

def service_info_node(state: AgentState):
    return {"final_response": {
        "type": "text",
        "text": "We offer:\n- ✨ Teeth Whitening\n- 🦷 Dental Implants\n- 😬 Invisalign",
        "buttons": [{"label": "Book Service", "payload": "ACTION_TRIGGER_BOOKING"}]
    }}

def emergency_node(state: AgentState):
    return {"final_response": {
        "type": "text",
        "text": "🚨 *Emergency\nCall **555-0199* immediately.",
        "buttons": [{"label": "Book Urgent Slot", "payload": "ACTION_TRIGGER_BOOKING"}]
    }}

# --- GRAPH ---
workflow = StateGraph(AgentState)
workflow.add_node("classifier", intent_classifier_node)
workflow.add_node("welcome", welcome_message_node)
workflow.add_node("find_doctor", retrieve_doctor_profile_node)
workflow.add_node("doctor_details", retrieve_doctor_details_node)
workflow.add_node("show_form", show_booking_form_node)
workflow.add_node("process_booking", process_booking_node)
workflow.add_node("services", service_info_node)
workflow.add_node("emergency", emergency_node)
workflow.add_node("general", general_chat_node)

def router(state):
    intent_map = {
        "welcome": "welcome", "find_doctor": "find_doctor", "doctor_details": "doctor_details",
        "show_form": "show_form", "process_booking": "process_booking", "services": "services",
        "emergency": "emergency", "general_chat": "general"
    }
    return intent_map.get(state["intent"], "general")

workflow.set_entry_point("classifier")
workflow.add_conditional_edges("classifier", router)
for node in ["welcome", "find_doctor", "doctor_details", "show_form", "process_booking", "services", "emergency", "general"]:
    workflow.add_edge(node, END)

app_graph = workflow.compile()