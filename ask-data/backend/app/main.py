# ask-data/backend/app/main.py
from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.query import QueryRequest  # 👈 Clean import from your schema folder

app = FastAPI(title="Bank ABC NL-to-SQL Core API")

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
    """Receives a validated natural language question from the schemas layer"""
    user_question = payload.question
    print(f"📥 Received a new question to translate: {user_question}")
    
    return {
        "received_question": user_question,
        "status": "In progress - awaiting AI translation logic"
    }