from langchain_groq import ChatGroq
from langchain.schema import HumanMessage, SystemMessage
from prompt_templates import SYSTEM_PROMPT
from langchain.schema import AIMessage
from config import MODEL_NAME, MAX_TOKENS, TEMPERATURE
import re
from datetime import datetime

class ChatbotEngine:
    def __init__(self):
        self.llm = ChatGroq(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )
        self.conversation_history = []
        self.system_message = SystemMessage(content=SYSTEM_PROMPT)
        self.conversation_history.append(self.system_message)
        
    def get_response(self, user_input):
        # Add user message to history
        self.conversation_history.append(HumanMessage(content=user_input))
        
        # Get response from LLM
        response = self.llm.invoke(self.conversation_history)
        
        # Add assistant response to history
        self.conversation_history.append(response)
        
        return response.content
    
    def extract_info(self, text, info_type):
        """Extract specific information from conversation using simple pattern matching"""
        if info_type == "name":
            patterns = [
                r"my name is ([A-Za-z\s]+)",
                r"i'm ([A-Za-z\s]+)",
                r"call me ([A-Za-z\s]+)",
                r"this is ([A-Za-z\s]+)",
            ]
        elif info_type == "problem":
            # Just return the latest user message as problem for simplicity
            for msg in reversed(self.conversation_history):
                if isinstance(msg, HumanMessage):
                    return msg.content
            return ""
        elif info_type == "doctor":
            patterns = [
                r"Dr\. ([A-Za-z\s]+)",
                r"doctor ([A-Za-z\s]+)",
            ]
        elif info_type == "date":
            patterns = [
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"(\d{1,2} (January|February|March|April|May|June|July|August|September|October|November|December) \d{4})",
                r"(today|tomorrow)",
            ]
        elif info_type == "time":
            patterns = [
                r"(\d{1,2}:\d{2} (AM|PM))",
                r"(\d{1,2} (AM|PM))",
                r"(\d{1,2} o'clock)",
            ]
        else:
            return None
            
        if info_type in ["problem"]:  # Special handling
            return self._extract_special_info(info_type)
            
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_special_info(self, info_type):
        """Special extraction methods for certain info types"""
        if info_type == "problem":
            # Look for the first user message after greeting
            for i, msg in enumerate(self.conversation_history):
                if isinstance(msg, HumanMessage) and i > 2:  # Skip initial messages
                    # Check if this might be describing a problem
                    if len(msg.content.split()) > 3:  # More than 3 words likely a problem description
                        return msg.content
        return None
    
    def validate_date_time(self, date_str, time_str):
        """Validate if the date and time are correct and within working hours"""
        from datetime import datetime
        
        try:
            # Parse date (handle different formats)
            if not date_str or not time_str:
                return False, "Please provide both date and time"
            
            # Normalize date first
            normalized_date = self.normalize_date(date_str)
            normalized_time = self.normalize_time(time_str)
            
            if not normalized_date or not normalized_time:
                return False, "I couldn't understand the date or time format"
            
            # Parse the datetime
            try:
                appointment_dt = datetime.strptime(f"{normalized_date} {normalized_time}", "%Y-%m-%d %H:%M")
            except:
                return False, "Invalid date or time format"
            
            # Check if it's in the future
            if appointment_dt < datetime.now():
                return False, "Please provide a future date and time"
            
            # Check day of week (0=Monday, 6=Sunday)
            day_of_week = appointment_dt.weekday()
            
            # Check working hours
            hour = appointment_dt.hour
            
            # Weekday hours: 9 AM - 6 PM (9-18)
            if day_of_week < 5:  # Monday-Friday
                if hour < 9 or hour >= 18:
                    return False, "Our clinic is open from 9:00 AM to 6:00 PM on weekdays"
            # Saturday hours: 10 AM - 4 PM (10-16)
            elif day_of_week == 5:  # Saturday
                if hour < 10 or hour >= 16:
                    return False, "Our clinic is open from 10:00 AM to 4:00 PM on Saturdays"
            else:  # Sunday
                return False, "Our clinic is closed on Sundays"
            
            return True, f"{appointment_dt.strftime('%A, %B %d, %Y at %I:%M %p')}"
            
        except Exception as e:
            return False, f"Error validating date: {str(e)}"
        def normalize_date(self, date_str):
            """Normalize date format to YYYY-MM-DD"""
            if not date_str:
                return None
                
            date_str = date_str.lower()
            
            # Handle relative dates
            if date_str == "today":
                return datetime.now().strftime("%Y-%m-%d")
            elif date_str == "tomorrow":
                from datetime import timedelta
                return (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Handle various date formats
            try:
                # Try different date formats
                for fmt in ("%m/%d/%Y", "%m-%d-%Y", "%d/%m/%Y", "%d-%m-%Y", 
                        "%B %d %Y", "%b %d %Y", "%d %B %Y", "%d %b %Y"):
                    try:
                        dt = datetime.strptime(date_str, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
            except:
                pass
                
            return date_str  # Return as-is if can't parse
        
    def normalize_time(self, time_str):
        """Normalize time format to HH:MM"""
        if not time_str:
            return None
            
        time_str = time_str.upper()
        
        # Handle various time formats
        try:
            # Try different time formats
            for fmt in ("%I:%M %p", "%I %p", "%H:%M"):
                try:
                    from datetime import datetime
                    dt = datetime.strptime(time_str, fmt)
                    return dt.strftime("%H:%M")
                except ValueError:
                    continue
        except:
            pass
            
        return time_str  # Return as-is if can't parse
    
    def reset_conversation(self):
        """Reset the conversation history"""
        self.conversation_history = [self.system_message]