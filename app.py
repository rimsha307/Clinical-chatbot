import streamlit as st
import requests
import json
from datetime import datetime
import re
from google_sheets_handler import GoogleSheetsHandler
import dateparser

# Page configuration
st.set_page_config(
    page_title="HealthCare Plus Clinic Chatbot",
    page_icon="🏥",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "patient_info" not in st.session_state:
    st.session_state.patient_info = {
        "name": None,
        "recommended_doctor": None,
        "appointment_date": None,
        "appointment_time": None
    }
if "conversation_state" not in st.session_state:
    st.session_state.conversation_state = "greeting"
if "appointment_saved" not in st.session_state:
    st.session_state.appointment_saved = False
if "last_processed_message" not in st.session_state:  # Track last processed message
    st.session_state.last_processed_message = None
import re

def clean_markdown(text: str) -> str:
    """Remove basic Markdown formatting like **bold** or _italic_."""
    if not text:
        return text
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)  # remove **bold**
    text = re.sub(r"\*(.*?)\*", r"\1", text)      # remove *italic*
    text = re.sub(r"_(.*?)_", r"\1", text)        # remove _italic_
    return text.strip()

# Track conversation progress
def update_conversation_state():
    """Update the conversation state based on collected information"""
    if not st.session_state.patient_info["name"]:
        st.session_state.conversation_state = "asking_name"
    elif not st.session_state.patient_info["recommended_doctor"]:
        st.session_state.conversation_state = "asking_doctor"
    elif not st.session_state.patient_info["appointment_date"] or not st.session_state.patient_info["appointment_time"]:
        st.session_state.conversation_state = "asking_time"
    else:
        st.session_state.conversation_state = "ready_to_confirm"

# API URL
API_URL = "http://localhost:8000"

# Initialize Google Sheets handler
@st.cache_resource
def get_sheets_handler():
    return GoogleSheetsHandler()

try:
    sheets_handler = get_sheets_handler()
    sheets_available = True
except Exception:
    sheets_available = False

# App title and description
st.title("🏥 HealthCare Plus Clinic Chatbot")
st.markdown("""
Welcome to our clinic's virtual assistant! I'm here to help you schedule an appointment 
with one of our specialists. Please chat with me to book your visit.
""")

# Doctors information
doctors_info = {
    "General Medicine": ["Dr. Smith", "Dr. Johnson"],
    "Cardiology": ["Dr. Williams", "Dr. Brown"],
    "Dermatology": ["Dr. Davis", "Dr. Miller"],
    "Orthopedics": ["Dr. Wilson", "Dr. Moore"],
    "Pediatrics": ["Dr. Taylor", "Dr. Anderson"],
    "Neurology": ["Dr. Thomas", "Dr. Jackson"]
}

# Create a container for the sidebar
sidebar = st.sidebar

with sidebar:
    st.header("🏥 HealthCare Plus Clinic")
    
    st.subheader("👨‍⚕️ Our Specialists")
    for specialty, doctors in doctors_info.items():
        with st.expander(f"{specialty}"):
            for doctor in doctors:
                st.write(f"• {doctor}")
    
    st.write("---")
    st.subheader("🕒 Working Hours")
    st.write("**Weekdays:** 9:00 AM - 6:00 PM")
    st.write("**Saturdays:** 10:00 AM - 4:00 PM")
    st.write("**Sundays:** Closed")
    
    st.write("---")
    st.subheader("📞 Contact Info")
    st.write("**Phone:** +1-555-123-4567")
    st.write("**Email:** info@healthcareplus.com")
    st.write("**Address:** 123 Medical Plaza, Health City, HC 12345")
    
    st.write("---")
    st.subheader("📋 Your Appointment Status")
    name_status = "✅" if st.session_state.patient_info["name"] else "❌"
    doctor_status = "✅" if st.session_state.patient_info["recommended_doctor"] else "❌"
    date_status = "✅" if st.session_state.patient_info["appointment_date"] else "❌"
    time_status = "✅" if st.session_state.patient_info["appointment_time"] else "❌"
    
    st.write(f"{name_status} **Name:** {st.session_state.patient_info['name'] or 'Not provided'}")
    st.write(f"{doctor_status} **Doctor:** {st.session_state.patient_info['recommended_doctor'] or 'Not chosen'}")
    st.write(f"{date_status} **Date:** {st.session_state.patient_info['appointment_date'] or 'Not set'}")
    st.write(f"{time_status} **Time:** {st.session_state.patient_info['appointment_time'] or 'Not set'}")
    
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.patient_info = {
            "name": None,
            "recommended_doctor": None,
            "appointment_date": None,
            "appointment_time": None
        }
        st.session_state.conversation_state = "greeting"
        st.session_state.appointment_saved = False


def save_to_google_sheets(patient_info):
    """Save appointment details to Google Sheets"""
    if not sheets_available:
        return False
    
    try:
        success = sheets_handler.add_appointment(
            patient_info["name"],
            patient_info.get("recommended_doctor", "Not specified"),
            patient_info.get("appointment_date", "Not specified"),
            patient_info.get("appointment_time", "Not specified")
        )
        return success
    except Exception as e:
        return False

def get_fallback_response(user_input, message_history):
    """Simple fallback responses when the main API is down"""
    user_input_lower = user_input.lower()
    
    # Check conversation history to maintain context
    last_responses = [msg["content"] for msg in message_history if msg["role"] == "assistant"][-2:]
    last_response = last_responses[-1] if last_responses else ""
    
    # Simple rule-based responses
    if any(greeting in user_input_lower for greeting in ["hi", "hello", "hey", "hola"]):
        st.session_state.conversation_state = "asking_name"
        return "Hello! Welcome to HealthCare Plus Clinic. I'm here to help you schedule an appointment. May I know your name please?"
    
    elif st.session_state.conversation_state == "asking_name":
        # If it's a reasonable name (not just "yes", "no", etc.)
        if (len(user_input.strip()) > 2 and 
            not any(word in user_input_lower for word in ["yes", "no", "ok", "sure", "hi", "hello"]) and
            not user_input_lower.isdigit()):
            
            st.session_state.patient_info["name"] = user_input.strip()
            update_conversation_state()
            return f"Nice to meet you, {user_input.strip()}! Which doctor or medical department would you like to visit?"
        else:
            return "Could you please tell me your name again?"
    
    elif st.session_state.conversation_state == "asking_doctor":
        if any(dept in user_input_lower for dept in ["general medicine", "general"]):
            st.session_state.patient_info["recommended_doctor"] = "Dr. Smith"
            update_conversation_state()
            return "Thank you! I recommend Dr. Smith from our general medicine department. When would you like to schedule your appointment?"
        elif any(dept in user_input_lower for dept in ["dermatology", "skin"]):
            st.session_state.patient_info["recommended_doctor"] = "Dr. Davis"
            update_conversation_state()
            return "Thank you! I recommend Dr. Davis from our dermatology department. When would you like to schedule your appointment?"
        else:
            return "Thank you! When would you like to schedule your appointment?"
    
    elif st.session_state.conversation_state == "asking_time":
        # Try to extract date and time
        date_pattern = r"(\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4})"
        time_pattern = r"(\d{1,2}:\d{2}\s*(am|pm))"
        
        date_match = re.search(date_pattern, user_input_lower)
        time_match = re.search(time_pattern, user_input_lower)
        
        if date_match:
            st.session_state.patient_info["appointment_date"] = date_match.group(1).title()
        
        if time_match:
            st.session_state.patient_info["appointment_time"] = time_match.group(1).upper()
        
        if st.session_state.patient_info["appointment_date"] and st.session_state.patient_info["appointment_time"]:
            update_conversation_state()
            return f"Thank you! I've scheduled your appointment for {st.session_state.patient_info['appointment_date']} at {st.session_state.patient_info['appointment_time']}. Please say 'confirm' to finalize your appointment."
        elif st.session_state.patient_info["appointment_date"]:
            return "Thank you! What time would you prefer for your appointment?"
        else:
            return "Thank you! When would you like to schedule your appointment?"
    
    elif any(word in user_input_lower for word in ["confirm", "yes", "sure", "finalize", "okay", "ok", "done", "book it", "yeah", "yep"]):
        # Try to save to Google Sheets
        if (st.session_state.patient_info["name"] and 
            st.session_state.patient_info["recommended_doctor"] and
            st.session_state.patient_info["appointment_date"] and
            st.session_state.patient_info["appointment_time"]):
            
            try:
                save_to_google_sheets(st.session_state.patient_info)
                return "Thank you! Your appointment has been confirmed and saved to our system. We'll see you then! 🏥"
            except:
                return "Thank you! Your appointment has been confirmed. We'll see you then! 🏥"
        else:
            return "I need a bit more information to confirm your appointment. Could you please provide your name, preferred doctor, date, and time?"
    
    else:
        st.session_state.conversation_state = "asking_name"
        return "I'm here to help you schedule an appointment. Could you please tell me your name so we can get started?"


def update_patient_info_from_conversation(user_input, bot_response):
    """Extract patient information from formatted confirmation messages"""
    bot_response_lower = bot_response.lower()
    
    # Check if we've already processed and saved this appointment
    if st.session_state.get("appointment_saved", False):
        print("Appointment already saved, skipping extraction")
        return None
    
    # Check if this is a formatted confirmation message with all details
    is_formatted_message = all([
        "date:" in bot_response_lower,
        "time:" in bot_response_lower,
        "doctor name:" in bot_response_lower or "doctor:" in bot_response_lower,
        "patient name:" in bot_response_lower or "name:" in bot_response_lower
    ])
    
    # Only extract information if this is a formatted confirmation message
    if is_formatted_message:
        print(f"Processing formatted confirmation message: {bot_response}")
        
        # Extract name - look for "Your Name: " or "Name: " followed by the name
        name_patterns = [
            r"patient name:\s*([^\n]+)",
            r"your name:\s*([^\n]+)",
            r"name:\s*([^\n]+)"
        ]
        
        for pattern in name_patterns:
            name_match = re.search(pattern, bot_response, re.IGNORECASE)
            if name_match:
                st.session_state.patient_info["name"] = clean_markdown(name_match.group(1))
                print(f"Extracted name: {st.session_state.patient_info['name']}")
                break
        
        # Extract doctor - look for "Doctor: " or "Doctor Name: " followed by the doctor's name
        doctor_pattern = r"(?:doctor name|doctor):\s*([^\n]+)"
        doctor_match = re.search(doctor_pattern, bot_response, re.IGNORECASE)
        
        if doctor_match:
            st.session_state.patient_info["recommended_doctor"] = clean_markdown(doctor_match.group(1))
            print(f"Extracted doctor: {st.session_state.patient_info['recommended_doctor']}")
        
        # Extract date - look for "Date: " followed by the date
        date_pattern = r"date:\s*([^\n]+)"
        date_match = re.search(date_pattern, bot_response, re.IGNORECASE)
        if date_match:
            st.session_state.patient_info["appointment_date"] = clean_markdown(date_match.group(1))
            print(f"Extracted date: {st.session_state.patient_info['appointment_date']}")
        
        # Extract time - look for "Time: " followed by the time
        time_pattern = r"time:\s*([^\n]+)"
        time_match = re.search(time_pattern, bot_response, re.IGNORECASE)
        if time_match:
            st.session_state.patient_info["appointment_time"] = clean_markdown(time_match.group(1))
            print(f"Extracted time: {st.session_state.patient_info['appointment_time']}")
        
        # Update conversation state based on what we extracted
        update_conversation_state()
        
        # If we successfully extracted all information, return a confirmation message
        if all([
            st.session_state.patient_info.get("name"),
            st.session_state.patient_info.get("recommended_doctor"),
            st.session_state.patient_info.get("appointment_date"),
            st.session_state.patient_info.get("appointment_time")
        ]):
            # Save to Google Sheets if all info is available AND not already saved
            if sheets_available and not st.session_state.get("appointment_saved", False):
                success = save_to_google_sheets(st.session_state.patient_info)
                if success:
                    st.session_state.appointment_saved = True  # Mark as saved
                    print("Appointment saved to Google Sheets")
                else:
                    print("Failed to save appointment to Google Sheets")
            
            confirmation_message = (
                f"✅ Thank you {st.session_state.patient_info['name']}! "
                f"Your appointment with {st.session_state.patient_info['recommended_doctor']} "
                f"has been booked on {st.session_state.patient_info['appointment_date']} at {st.session_state.patient_info['appointment_time']}."
            )
            st.session_state.conversation_state = "done"
            return confirmation_message
    
    # If this isn't a formatted message, don't extract anything
    print("Not a formatted confirmation message, skipping extraction")
    return None

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input - OPTIMIZED VERSION
if prompt := st.chat_input("Type your message here..."):
    # Only process if this is a new message
    if prompt != st.session_state.get("last_processed_message", ""):
        st.session_state.last_processed_message = prompt
        
        # Add user message immediately
        st.session_state.messages.append({"role": "user", "content": prompt})

        
        # Display user message immediately
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get chatbot response (this is where the delay happens)
        try:
            # Show a spinner while waiting for API response
            with st.spinner("Thinking..."):
                response = requests.post(
                    f"{API_URL}/chat",
                    json={"message": prompt},
                    timeout=8  # Reasonable timeout
                )
                
            if response.status_code == 200:
                bot_response = response.json()["response"]
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(bot_response)

                # Add to chat history
                st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
                # Extract info (non-blocking, happens after response is shown)
                if not st.session_state.get("appointment_saved", False):
                    update_patient_info_from_conversation(prompt, bot_response)
                
        except requests.exceptions.RequestException as e:
            # Show fallback immediately
            fallback_response = get_fallback_response(prompt, st.session_state.messages)
            with st.chat_message("assistant"):
                st.markdown(fallback_response)
            st.session_state.messages.append({"role": "assistant", "content": fallback_response})
        
 