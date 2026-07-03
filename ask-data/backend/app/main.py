from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

app = FastAPI(title="Bank ABC NL-to-SQL Core API")

# 📥 1. Define what the incoming request data must look like
class QueryRequest(BaseModel):
    question: str  # The plain English question from the user (e.g., "Show me top 5 clients")

# --- Existing Routes (Kept Exactly the Same) ---

@app.get("/")
def read_root():
    """Friendly landing page for the base URL to prevent 404s"""
    return {
        "message": "Welcome to the Bank ABC NL-to-SQL Core API",
        "status": "online",
        "documentation": "/docs",
        "health_check": "/health"
    }

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Exercises the Cloudflare tunnel and checks connectivity to mysql.ksmd.my.id"""
    try:
        result = db.execute(text("SELECT 1;")).scalar()
        if result == 1:
            return {
                "status": "healthy",
                "database_connection": "connected",
                "tunnel": "active"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database_error": str(e)
        }

# --- 🚀 The New AI Placeholder Route ---

@app.post("/ask")
def ask_ai(payload: QueryRequest, db: Session = Depends(get_db)):
    """
    Receives a natural language question, validates it via Pydantic,
    and prepares to pass it to the text-to-SQL translation engine.
    """
    user_question = payload.question
    
    # Right now, we just print it to the logs and return it back to confirm receipt
    print(f"📥 Received a new question to translate: {user_question}")
    
    return {
        "received_question": user_question,
        "status": "In progress - awaiting AI translation logic"
    }