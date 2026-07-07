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
    
def get_database_schema() -> str:
    """
    Retrieves the structural enterprise schema configuration, table layouts, 
    available columns, and relationships from the shared domain configuration file.
    """
    # Navigate up from mcp_server/app/tools/ to look for domain_config.yaml
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Try looking in the parent directory or root workspace
    paths_to_check = [
        os.path.join(current_dir, "..", "..", "domain_config.yaml"),
        os.path.join(current_dir, "..", "..", "..", "domain_config.yaml"),
        "domain_config.yaml"
    ]
    
    for config_path in paths_to_check:
        normalized_path = os.path.abspath(config_path)
        if os.path.exists(normalized_path):
            try:
                with open(normalized_path, "r") as f:
                    return f.read()
            except Exception as e:
                return f"Error reading configuration file at {normalized_path}: {str(e)}"
                
    return "Error: Enterprise configuration mapping file 'domain_config.yaml' could not be located."