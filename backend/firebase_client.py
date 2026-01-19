import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, Dict
import os

# 1. Initialize Firebase (Singleton pattern to prevent re-init errors)
if not firebase_admin._apps:
    # Path to your JSON key file
    cred_path = "firebase_credentials.json"
    
    if os.path.exists(cred_path):
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
    else:
        print(f"[ERROR] '{cred_path}' not found. Please download it from Firebase Console.")

# 2. Get Database Client
def get_db():
    try:
        return firestore.client()
    except Exception as e:
        print(f"Firebase Init Error: {e}")
        return None

# --- Main Functions ---

def save_conversation_state(state: Dict):
    """Save conversation state to Firestore (Upsert)"""
    session_id = state.get("session_id")
    if not session_id:
        return

    db = get_db()
    if not db: 
        return

    # Data to save
    data = {
        "session_id": session_id,
        "department": state.get("department", ""),
        "location": state.get("location", ""),
        "issue_description": state.get("issue_description", ""),
        "severity_level": state.get("severity_level", 0),
        "status": state.get("status", "in_progress"),
        "last_message": state.get("user_message", ""),
        "ai_response": state.get("ai_response", ""),
        "updated_at": firestore.SERVER_TIMESTAMP
    }

    try:
        # .document(session_id) creates a doc with that specific ID
        # merge=True means "Update fields if exists, Create if not"
        db.collection("conversations").document(session_id).set(data, merge=True)
    except Exception as e:
        print(f"[ERROR] Firebase Save Error: {e}")

def get_conversation_state(session_id: str) -> Optional[Dict]:
    """Retrieve conversation state"""
    db = get_db()
    if not db: 
        return None

    try:
        doc_ref = db.collection("conversations").document(session_id)
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            # Return only valid state fields (exclude timestamps)
            return {
                "session_id": data.get("session_id", ""),
                "department": data.get("department", ""),
                "location": data.get("location", ""),
                "issue_description": data.get("issue_description", ""),
                "severity_level": data.get("severity_level", 0),
                "status": data.get("status", "in_progress"),
                "user_message": data.get("last_message", ""),
                "ai_response": data.get("ai_response", ""),
                "last_message": data.get("last_message", ""),
                "missing_fields": []
            }
    except Exception as e:
        print(f"[ERROR] Firebase Read Error: {e}")
    
    return None

def save_report(report: Dict):
    """Save completed report to Firestore"""
    db = get_db()
    if not db:
        return

    try:
        # Add a timestamp
        report["created_at"] = firestore.SERVER_TIMESTAMP
        # .add() automatically generates a unique ID for the report
        db.collection("reports").add(report)
        print("[OK] Report saved to Firebase!")
    except Exception as e:
        print(f"[ERROR] Failed to save report: {e}")