import os
import json
from sqlalchemy import create_engine, text

# 1. Fetch connection parameters from environment variables with safe fallbacks
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "bank_abc_analytics")

# Establish connection string pointing strictly to your localhost background tunnel
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@localhost:3306/{DB_NAME}"
)

# 2. Initialize the database engine with self-healing pooling options
db_engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,  # Discovers immediately if the Cloudflare tunnel blips
    pool_recycle=3600
)

def execute_banking_query(sql_query: str) -> str:
    """
    Executes a read-only MySQL SELECT statement against the live bank analytics database 
    through the secure tunnel and returns rows formatted as a JSON string.
    Only SELECT queries are authorized.
    """
    # Clean up any potential markdown formatting syntax applied by the LLM client
    query = sql_query.strip().replace("```sql", "").replace("```", "").strip()
    
    # --- MANDATORY SECURITY GUARDRAIL ---
    # Intercept and block any mutation attempts (DROP, DELETE, UPDATE, INSERT)
    if not query.lower().startswith("select"):
        return "Security Violation Error: Only read-only SELECT queries are authorized on this endpoint."
        
    try:
        with db_engine.connect() as connection:
            result = connection.execute(text(query))
            
            # Map the raw database tuples into a clean dictionary list (Column Name -> Value)
            columns = result.keys()
            records = [dict(zip(columns, row)) for row in result.fetchall()]
            
            # Return the records as a standardized JSON string payload
            return json.dumps(records, default=str)
            
    except Exception as e:
        return f"Database Execution Error: {str(e)}"