import os
from typing import TypedDict, Annotated, Literal, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from webhook_client import send_webhook
from dotenv import load_dotenv
import json
from firebase_client import save_conversation_state, get_conversation_state, save_report

# Load environment variables
load_dotenv()

# Initialize OpenAI client lazily
_llm = None

def get_llm():
    """Get or create the OpenAI LLM instance"""
    global _llm
    if _llm is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        _llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=api_key)
    return _llm

# State definition
class ConversationState(TypedDict):
    session_id: str
    user_message: str
    ai_response: str
    department: str
    location: str
    issue_description: str
    severity_level: int
    missing_fields: list
    status: str
    last_message: str


def classify_intent(message: str) -> str:
    """Classify user intent into department categories"""
    message_lower = message.lower()
    
    # Primary: Keyword-based classification (works without OpenAI)
    traffic_keywords = ["traffic", "road", "congestion", "parking", "accident", "pothole", "highway", "intersection", "stop sign", "traffic light", "speed limit", "blocked", "blockage"]
    waste_keywords = ["trash", "garbage", "waste", "recycling", "litter", "dump", "bin", "rubbish", "refuse", "collection", "overflowing", "smell", "smells"]
    energy_keywords = ["park", "green", "energy", "electricity", "pollution", "tree", "environment", "solar", "wind", "renewable", "carbon", "emission", "light", "lights", "street light", "streetlight", "street lights", "lamp", "lamps", "power", "utility"]
    
    if any(word in message_lower for word in traffic_keywords):
        return "traffic_dept"
    elif any(word in message_lower for word in waste_keywords):
        return "waste_dept"
    elif any(word in message_lower for word in energy_keywords):
        return "energy_dept"
    
    # Secondary: Try OpenAI if available (with error handling)
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a routing assistant. Classify the user's message into one of these departments:
            - traffic_dept: For congestion, road issues, traffic lights, parking, accidents, road maintenance
            - waste_dept: For trash, recycling, garbage collection, waste disposal, litter
            - energy_dept: For parks, green spaces, electricity issues, pollution, environmental concerns
            
            Respond with ONLY one word: traffic_dept, waste_dept, or energy_dept"""),
            ("user", "{message}")
        ])
        
        chain = prompt | get_llm()
        response = chain.invoke({"message": message}).content.strip().lower()
        
        if "traffic_dept" in response or "traffic" in response:
            return "traffic_dept"
        elif "waste_dept" in response or "waste" in response:
            return "waste_dept"
        elif "energy_dept" in response or "energy" in response:
            return "energy_dept"
    except Exception as e:
        # OpenAI unavailable (quota, API key, etc.) - use keyword fallback
        print(f"OpenAI classification failed: {str(e)}. Using keyword-based routing.")
        pass
    
    # Default fallback to traffic
    return "traffic_dept"


def extract_location(message: str) -> Optional[str]:
    """Extract location from message"""
    import re
    
    message_clean = message.strip()
    
    # If message is reasonably short and not just a number, treat it as location
    # This handles answers like "near railway station", "highway 101", "downtown", etc.
    if 3 <= len(message_clean) <= 200:
        # Check if it's clearly NOT a location (single words that are responses)
        simple_responses = ["yes", "no", "ok", "okay", "sure", "thanks", "thanks!", "great", "good"]
        if message_clean.lower() not in simple_responses:
            return message_clean
    
    # Enhanced pattern matching for structured locations
    location_patterns = [
        # Street addresses with numbers
        r'\b\d+\s+\w+\s+(street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|way|place|pl)\b',
        # Named roads/streets (e.g., "MG Road", "Main Street")
        r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)\s+(road|street|st|avenue|ave|rd|boulevard|blvd|drive|dr)\b',
        # Landmarks with "at", "near", "on", "in" (e.g., "at Central Park", "near Railway Station")
        r'\b(at|near|on|in)\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*(?:,\s*[A-Z][A-Za-z]+)?)',
        # Landmarks without prepositions (e.g., "Central Park, Jaipur")
        r'\b([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)+)(?:,\s*[A-Z][A-Za-z]+)?',
        # Coordinates
        r'\b\d+\.\d+,\s*-?\d+\.\d+\b',
    ]
    
    for pattern in location_patterns:
        matches = re.finditer(pattern, message_clean, re.IGNORECASE)
        for match in matches:
            location = match.group(0).strip()
            # Filter out common false positives
            if location.lower() not in ["the", "this", "that", "there", "here"]:
                # Clean up "at/near/on/in" prefix but keep the location
                location = re.sub(r'^(at|near|on|in)\s+', '', location, flags=re.IGNORECASE)
                if len(location) > 3:  # Minimum meaningful location
                    return location
    
    # Fallback: return the message if it's of reasonable length
    if len(message_clean) >= 3:
        return message_clean
    
    return None


def extract_severity(message: str) -> Optional[int]:
    """Extract severity level (1-10) from message"""
    import re
    
    message_clean = message.strip()
    
    # Priority 1: Check for standalone number first (most likely when answering "on a scale of 1-10")
    if message_clean.isdigit():
        severity = int(message_clean)
        if 1 <= severity <= 10:
            return severity
    
    # Priority 2: Look for numbers within text
    # Patterns: "severity 7", "level 5", "7/10", "7 out of 10", etc.
    severity_patterns = [
        r'(\d+)\s*(?:out\s+of\s+10|/10)',  # "7 out of 10" or "7/10"
        r'(?:severity|level|score|rate)\s*:?\s*(\d+)',  # "severity: 7" or "level 7"
        r'(?:is|are|been)\s+(\d+)',  # "is 7"
    ]
    
    for pattern in severity_patterns:
        match = re.search(pattern, message_clean, re.IGNORECASE)
        if match:
            try:
                severity = int(match.group(1))
                if 1 <= severity <= 10:
                    return severity
            except:
                pass
    
    # Priority 3: Any number 1-10 in the message (if short response)
    if len(message_clean) < 20:  # Only for short responses
        numbers = re.findall(r'\b([1-9]|10)\b', message_clean)
        if numbers:
            try:
                severity = int(numbers[0])
                if 1 <= severity <= 10:
                    return severity
            except:
                pass
    
    # Priority 4: Infer from keywords only if message is descriptive
    message_lower = message_clean.lower()
    
    # Don't infer from keywords if it looks like a direct answer to severity question
    if len(message_clean) <= 5:
        return None
    
    critical_keywords = ["critical", "urgent", "emergency", "severe", "dangerous", "immediate", "life-threatening"]
    high_keywords = ["serious", "major", "important", "significant", "bad", "broken"]
    medium_keywords = ["moderate", "medium", "somewhat", "noticeable", "moderate"]
    low_keywords = ["minor", "small", "slight", "trivial", "inconvenience", "little"]
    
    if any(word in message_lower for word in critical_keywords):
        return 9
    elif any(word in message_lower for word in high_keywords):
        return 7
    elif any(word in message_lower for word in medium_keywords):
        return 5
    elif any(word in message_lower for word in low_keywords):
        return 3
    
    # Return None if nothing found (so system asks for it)
    return None


def start_node(state: ConversationState) -> ConversationState:
    """Initial node that receives user input"""
    return state


def is_greeting(message: str) -> bool:
    """Check if message is a greeting or casual conversation"""
    message_lower = message.lower().strip()
    
    if any(ch.isdigit() for ch in message_lower):
        return False
    greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", 
                 "greetings", "hi there", "hello there", "hey there", "what's up", "sup"]
    
    # Check for issue keywords first - if present, it's not just a greeting
    traffic_keywords = ["traffic", "road", "congestion", "parking", "accident", "pothole", "blocked"]
    waste_keywords = ["trash", "garbage", "waste", "recycling", "litter", "overflowing", "smell"]
    energy_keywords = ["park", "green", "energy", "electricity", "pollution", "light", "lights", "broken"]
    
    has_issue_keywords = any(word in message_lower for word in traffic_keywords + waste_keywords + energy_keywords)
    
    # If it has issue keywords, it's not just a greeting (even if it starts with hi/hello)
    if has_issue_keywords:
        return False
    
    # Check if it's just a greeting
    if message_lower in greetings:
        return True
    
    # Check if it starts with greeting but has no issue keywords
    if message_lower.startswith(("hi ", "hello ", "hey ")) and not has_issue_keywords:
        # If it's just "hi" or "hi" + very short text, treat as greeting
        words = message_lower.split()
        if len(words) <= 3:
            return True
    
    # Check if message is very short and doesn't contain issue keywords
    if len(message_lower) < 15 and not has_issue_keywords:
        return True
    
    return False


def router_node(state: ConversationState) -> ConversationState:
    """Route message to appropriate department"""
    session_id = state["session_id"]
    user_message = state["user_message"]
    existing_state = get_conversation_state(session_id)
    
    # Only treat as greeting when starting a brand new session
    if not existing_state and is_greeting(user_message):
        state["ai_response"] = "Hi! I'm here to help you report issues to your city departments. What problem would you like to report?"
        state["status"] = "greeting"
        state["department"] = ""  # No department yet for greeting
        save_conversation_state(state)
        return state
    
    # Load existing state if available
    if existing_state:
        # Preserve the current user message and session ID
        current_session = state["session_id"]
        current_user_message = state["user_message"]
        
        # Update state with previous conversation data
        state.update(existing_state)
        
        # Restore current session and message
        state["session_id"] = current_session
        state["user_message"] = current_user_message
        
        # IMPORTANT: Only reclassify department if status is "greeting"
        # If we're already collecting data (awaiting_severity, awaiting_location, etc),
        # keep the department from the existing state
        if state.get("status") == "greeting":
            state["department"] = classify_intent(user_message)
        # Otherwise, department is already set from existing_state.update() above
    else:
        # No existing state - classify the intent
        state["department"] = classify_intent(user_message)
    
    return state


def traffic_node(state: ConversationState) -> ConversationState:
    """Handle traffic department queries"""
    return process_department_node(state, "traffic_dept", "traffic")


def waste_node(state: ConversationState) -> ConversationState:
    """Handle waste management department queries"""
    return process_department_node(state, "waste_dept", "waste")


def energy_node(state: ConversationState) -> ConversationState:
    """Handle green energy & spaces department queries"""
    return process_department_node(state, "energy_dept", "green_energy")


def process_department_node(state: ConversationState, dept_code: str, dept_name: str) -> ConversationState:
    """Generic department node processor"""
    # Extract message before updating state
    message_text = state.get("user_message", "").strip()
    
    # Update department
    state["department"] = dept_code
    
    # If conversation was completed, restart it
    if state.get("status") == "complete":
        state["issue_description"] = ""
        state["location"] = ""
        state["severity_level"] = 0
        state["status"] = "in_progress"
    
    # Empty message - ask for issue description
    if not message_text:
        state["ai_response"] = "What problem would you like to report? Please describe the issue."
        state["status"] = "awaiting_issue"
        save_conversation_state(state)
        return state
    
    # STATE: Greeting or starting new issue - ask for severity after recording issue
    if state.get("status") in ["greeting", "in_progress", "", None]:
        state["issue_description"] = message_text
        state["ai_response"] = "On a scale of 1-10, how severe is this issue? (1 = minor, 10 = critical)"
        state["status"] = "awaiting_severity"
        save_conversation_state(state)
        return state
    
    # STATE: Awaiting issue description
    if state.get("status") == "awaiting_issue":
        state["issue_description"] = message_text
        state["ai_response"] = "On a scale of 1-10, how severe is this issue? (1 = minor, 10 = critical)"
        state["status"] = "awaiting_severity"
        save_conversation_state(state)
        return state
    
    # STATE: Awaiting severity level
    if state.get("status") == "awaiting_severity":
        severity = extract_severity(message_text)
        
        if not severity:
            # Re-ask for severity
            state["ai_response"] = "Please provide a severity rating from 1-10. (1 = minor, 10 = critical)"
            state["status"] = "awaiting_severity"
            save_conversation_state(state)
            return state
        
        # Valid severity received
        state["severity_level"] = severity
        state["ai_response"] = "Thank you. Could you please provide the location (address, coordinates, or landmark) where this is occurring?"
        state["status"] = "awaiting_location"
        save_conversation_state(state)
        return state
    
    # STATE: Awaiting location
    if state.get("status") == "awaiting_location":
        location = extract_location(message_text)
        
        if not location or len(location.strip()) < 3:
            state["ai_response"] = "Could you please provide the location (address, street name, landmark, or coordinates)?"
            state["status"] = "awaiting_location"
            save_conversation_state(state)
            return state
        
        # Valid location received - submit report
        state["location"] = location.strip()
        dept_display = dept_name.replace("_", " ").replace("dept", "").strip()
        state["ai_response"] = f"Thank you! I've collected all the information about your {dept_display} report. Your report has been submitted to the appropriate department."
        state["status"] = "complete"
        save_conversation_state(state)
        
        # Save to database and send webhook
        report_data = {
            "session_id": state["session_id"],
            "department": dept_name,
            "location": state["location"],
            "issue_description": state["issue_description"],
            "severity_level": state["severity_level"]
        }
        save_report(report_data)
        
        webhook_data = {
            "location": state["location"],
            "issue_description": state["issue_description"],
            "severity_level": state["severity_level"],
            "department": dept_name
        }
        send_webhook(webhook_data)
        save_conversation_state(state)
        return state
    
    # Default fallback
    dept_display = dept_name.replace("_", " ").replace("dept", "").strip()
    state["ai_response"] = f"I can help you report a {dept_display} issue. Could you please describe what the problem is?"
    state["status"] = "awaiting_issue"
    save_conversation_state(state)
    return state


def should_continue(state: ConversationState) -> str:
    """Determine next node based on department"""
    # After greeting, if we have a new message with a department, proceed to that department
    status = state.get("status", "")
    dept = state.get("department", "")
    
    # If status is greeting, only end if we're not trying to route to a department
    # (i.e., if they sent a new message with a real issue, we should route it)
    if status == "greeting" and dept == "":
        return "__end__"
    
    if dept == "traffic_dept":
        return "traffic_node"
    elif dept == "waste_dept":
        return "waste_node"
    elif dept == "energy_dept":
        return "energy_node"
    
    return "__end__"


# Build the graph
workflow = StateGraph(ConversationState)

workflow.add_node("start_node", start_node)
workflow.add_node("router_node", router_node)
workflow.add_node("traffic_node", traffic_node)
workflow.add_node("waste_node", waste_node)
workflow.add_node("energy_node", energy_node)

workflow.set_entry_point("start_node")
workflow.add_edge("start_node", "router_node")
workflow.add_conditional_edges(
    "router_node",
    should_continue,
    {
        "traffic_node": "traffic_node",
        "waste_node": "waste_node",
        "energy_node": "energy_node",
        "__end__": END,
    }
)
workflow.add_edge("traffic_node", END)
workflow.add_edge("waste_node", END)
workflow.add_edge("energy_node", END)

app = workflow.compile()


async def process_message(message: str, session_id: str = None) -> dict:
    """Process a user message through the LangGraph workflow"""
    import uuid
    import asyncio
    import concurrent.futures
    
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Initialize state
    state = {
        "session_id": session_id,
        "user_message": message,
        "ai_response": "",
        "department": "",
        "location": "",
        "issue_description": "",
        "severity_level": 0,
        "missing_fields": [],
        "status": "in_progress",
        "last_message": message
    }
    
    # Run workflow in executor to avoid blocking
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = await loop.run_in_executor(executor, app.invoke, state)
    
    # Ensure we always have a response
    ai_response = result.get("ai_response", "")
    if not ai_response:
        ai_response = "I'm processing your request. Please provide more details."
    
    return {
        "response": ai_response,
        "session_id": result.get("session_id", session_id),
        "department": result.get("department", "").replace("_dept", ""),
        "status": result.get("status", "in_progress")
    }

