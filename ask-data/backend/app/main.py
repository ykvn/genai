from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

app = FastAPI(title="Bank ABC NL-to-SQL Core API")

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    A live test route that exercises the Cloudflare tunnel 
    and checks connectivity to mysql.ksmd.my.id
    """
    try:
        # Test query to check the DB connection pool
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