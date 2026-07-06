# ask-data/backend/app/main.py
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.query import QueryRequest
from app.services.translator import SQLTranslationService

app = FastAPI(title="Bank ABC NL-to-SQL Core API")
translator_service = SQLTranslationService()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Bank ABC NL-to-SQL Core API", "status": "online"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1;")).scalar()
        if result == 1:
            return {"status": "healthy", "database_connection": "connected", "tunnel": "active"}
    except Exception as e:
        return {"status": "unhealthy", "database_error": str(e)}

@app.post("/ask")
def ask_ai(payload: QueryRequest, db: Session = Depends(get_db)):
    """Processes natural language questions all the way through prompt construction and SQL prediction"""
    try:
        user_question = payload.question
        
        # 🚀 Invoke the LLM pipeline (calls vLLM or uses the test fallback smoothly)
        generated_sql = translator_service.generate_sql(user_question)
        
        return {
            "question": user_question,
            "status": "SQL Code Generation Successful",
            "predicted_sql": generated_sql
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Translation Layer Error: {str(e)}")