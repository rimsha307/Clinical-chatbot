from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot_engine import ChatbotEngine
from google_sheets_handler import GoogleSheetsHandler
import json
import logging


app = FastAPI(title="Clinical Chatbot API")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
chatbot = ChatbotEngine()
try:
    sheets_handler = GoogleSheetsHandler()
    sheets_available = True
    logger.info("Google Sheets integration enabled")
except Exception as e:
    sheets_handler = None
    sheets_available = False
    logger.warning(f"Google Sheets not available: {str(e)}")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    session_id: str = None

class AppointmentRequest(BaseModel):
    patient_name: str
    problem: str
    recommended_doctor: str
    appointment_date: str
    appointment_time: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        logger.info(f"Received message: {request.message}")
        response = chatbot.get_response(request.message)
        logger.info(f"Generated response: {response}")
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        # Return a friendly error message instead of raising exception
        return ChatResponse(response="I apologize, I'm having some technical difficulties right now. Could you please try again or tell me how I can help you?")

@app.post("/schedule_appointment")
async def schedule_appointment(request: AppointmentRequest):
    try:
        # Normalize date and time
        normalized_date = chatbot.normalize_date(request.appointment_date)
        normalized_time = chatbot.normalize_time(request.appointment_time)
        
        # Add to Google Sheets
        success = sheets_handler.add_appointment(
            request.patient_name,
            request.problem,
            request.recommended_doctor,
            normalized_date or request.appointment_date,
            normalized_time or request.appointment_time
        )
        
        if success:
            return {"message": "Appointment scheduled successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to schedule appointment")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scheduling appointment: {str(e)}")
        
        if not sheets_available or sheets_handler is None:
            raise HTTPException(status_code=503, detail="Google Sheets integration not available")


@app.post("/save_appointment")
async def save_appointment(request: AppointmentRequest):
    try:
        if not sheets_available:
            return {"message": "Google Sheets integration not available"}
        
        # Normalize date and time
        normalized_date = chatbot.normalize_date(request.appointment_date)
        normalized_time = chatbot.normalize_time(request.appointment_time)
        
        # Add to Google Sheets
        success = sheets_handler.add_appointment(
            request.patient_name,
            request.problem,
            request.recommended_doctor,
            normalized_date or request.appointment_date,
            normalized_time or request.appointment_time
        )
        
        if success:
            return {"message": "Appointment saved to Google Sheets successfully"}
        else:
            return {"message": "Failed to save appointment"}
            
    except Exception as e:
        logger.error(f"Error saving appointment: {str(e)}")
        return {"message": f"Error saving appointment: {str(e)}"}

@app.get("/")
async def root():
    return {"message": "Clinical Chatbot API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)