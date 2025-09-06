import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from config import GOOGLE_SHEETS_CREDENTIALS, SPREADSHEET_ID, SHEET_NAME
from datetime import datetime

class GoogleSheetsHandler:
    def __init__(self):
        self.scope = [
            "https://spreadsheets.google.com/feeds", 
            "https://www.googleapis.com/auth/drive"
        ]

        # Load credentials from JSON file path
        if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS):
            raise FileNotFoundError(f"Google Sheets credentials file not found: {GOOGLE_SHEETS_CREDENTIALS}")

        self.creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_SHEETS_CREDENTIALS, self.scope
        )
        self.client = gspread.authorize(self.creds)

        # 🔎 Debug: list available worksheets
        spreadsheet = self.client.open_by_key(SPREADSHEET_ID)
        print("DEBUG: Available worksheets ->", [ws.title for ws in spreadsheet.worksheets()])

        # Try to open worksheet
        self.sheet = spreadsheet.worksheet(SHEET_NAME)
        
        # Ensure headers exist
        headers = ["Timestamp", "Patient Name", "Recommended Doctor", "Appointment Date", "Appointment Time"]
        if self.sheet.row_values(1) != headers:
            self.sheet.insert_row(headers, 1)
    
    def add_appointment(self, patient_name, recommended_doctor, appointment_date, appointment_time):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [timestamp, patient_name, recommended_doctor, appointment_date, appointment_time]
        self.sheet.append_row(row_data)
        return True
    
        # In your GoogleSheetsHandler class, add this method:
    def get_existing_appointments(self):
        """Get all existing appointments from the sheet"""
        try:
            result = self.sheet.get_all_values()
            return result[1:] if len(result) > 1 else []  # Skip header row
        except Exception as e:
            print(f"Error reading existing appointments: {e}")
            return []

def save_to_google_sheets(patient_info):
    """Save appointment details to Google Sheets with duplicate prevention"""
    if not sheets_available:
        return False
    
    try:
        # Check if this exact appointment already exists (excluding timestamp)
        existing_data = sheets_handler.get_existing_appointments()
        current_appointment = (
            patient_info["name"],
            patient_info.get("recommended_doctor", "Not specified"),
            patient_info.get("appointment_date", "Not specified"),
            patient_info.get("appointment_time", "Not specified")
        )
        
        # Convert to string for comparison (skip timestamp which is first element)
        current_appointment_str = " | ".join(str(item) for item in current_appointment)
        
        # Check if this appointment already exists (skip timestamp in comparison)
        for row in existing_data:
            # Skip the timestamp (first element) when comparing
            if len(row) >= 5:  # Make sure row has enough elements
                row_str = " | ".join(str(item) for item in row[1:5])  # Skip timestamp, take next 4 elements
                if row_str == current_appointment_str:
                    print("Duplicate appointment detected, not saving")
                    return True  # Return True as we don't want to show an error
        
        # If not a duplicate, save it
        success = sheets_handler.add_appointment(
            patient_info["name"],
            patient_info.get("recommended_doctor", "Not specified"),
            patient_info.get("appointment_date", "Not specified"),
            patient_info.get("appointment_time", "Not specified")
        )
        return success
    except Exception as e:
        print(f"Error saving to Google Sheets: {e}")
        return False