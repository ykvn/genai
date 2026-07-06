# ask-data/backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.query import QueryRequest
from app.services.translator import SQLTranslationService  # 👈 Import our new service

app = FastAPI(title="Bank ABC NL-to-SQL Core API")

# Initialize the service instance once when the application starts
translator_service = SQLTranslationService()

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

@app.post("/ask")
def ask_ai(payload: QueryRequest, db: Session = Depends(get_db)):
    """Receives a natural language question and generates the LLM context prompt"""
    try:
        user_question = payload.question
        
        # 🏗️ Generate the complete system prompt layout using our YAML config data
        system_context = translator_service.build_llm_system_context()
        
        # Return the question and the prompt to verify everything links up perfectly
        return {
            "received_question": user_question,
            "status": "Metadata compilation successful",
            "generated_llm_system_prompt": system_context
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation Service Error: {str(e)}")