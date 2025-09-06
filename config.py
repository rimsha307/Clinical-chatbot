import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

# Google Sheets Configuration
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1J8lKX67070VMjAa5BodZD9AEFP-CTGQwGT9Ff27lh7k")
SHEET_NAME = os.getenv("SHEET_NAME", "Sheet1")

# Model Configuration
MODEL_NAME = "llama-3.1-8b-instant"
MAX_TOKENS = 1024
TEMPERATURE = 0.3

# Clinic Details
CLINIC_DETAILS_FILE = "clinic_details.json"