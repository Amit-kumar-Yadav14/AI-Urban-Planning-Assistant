from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from langgraph_workflow import process_message, classify_intent

load_dotenv()

app = FastAPI(title="Urban Planning Assistant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    department: Optional[str] = None
    status: str


class ClassificationRequest(BaseModel):
    message: str


class ClassificationResponse(BaseModel):
    message: str
    department: str
    confidence: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    import traceback
    try:
        result = await process_message(request.message, request.session_id)
        return ChatResponse(
            response=result["response"],
            session_id=result["session_id"],
            department=result.get("department"),
            status=result.get("status", "in_progress")
        )
    except Exception as e:
        error_detail = f"{str(e)}\n\n{traceback.format_exc()}"
        print(f"Error in chat endpoint: {error_detail}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/classify", response_model=ClassificationResponse)
async def classify_endpoint(request: ClassificationRequest):
    """Classify user message into one of three departments: traffic, waste, energy"""
    try:
        department = classify_intent(request.message)
        
        # Map department codes to display names
        dept_map = {
            "traffic_dept": "Traffic",
            "waste_dept": "Waste Management",
            "energy_dept": "Green Energy & Spaces"
        }
        
        dept_name = dept_map.get(department, "Unknown")
        
        return ClassificationResponse(
            message=request.message,
            department=dept_name,
            confidence="high"
        )
    except Exception as e:
        print(f"Error in classify endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    return {"status": "healthy", "departments": ["Traffic", "Waste Management", "Green Energy & Spaces"]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

