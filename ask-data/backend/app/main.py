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
    """
    Processes natural language questions, translates them to SQL, 
    and executes the query against the database to return real live records.
    """
    try:
        user_question = payload.question
        
        # 1. Translate the English question into a SQL query string
        generated_sql = translator_service.generate_sql(user_question)
        
        # 2. Execute the query directly on your home MySQL server via SQLAlchemy
        # We wrap the string query in SQLAlchemy's text() function for safety
        db_result = db.execute(text(generated_sql))
        
        # 3. Convert the database rows into a list of dictionaries so FastAPI can turn it into JSON
        # db_result.mappings() allows us to access columns by their name keys automatically
        records = [dict(row) for row in db_result.mappings()]
        
        return {
            "question": user_question,
            "status": "Success",
            "predicted_sql": generated_sql,
            "row_count": len(records),
            "data": records  # 👈 This will hold your live database rows!
        }
        
    except Exception as e:
        # Catch any database errors (like bad syntax or missing tables) and report them cleanly
        raise HTTPException(
            status_code=500, 
            detail=f"Database Execution Failure: {str(e)}"
        )