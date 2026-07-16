import os
import json

# 🔌 Import the validated Cloudera Impala execution utility
from app.tools.impala_client import execute_query

def execute_banking_query(sql_query: str) -> str:
    """
    Executes a read-only Cloudera Impala SELECT statement against the live 
    analytical warehouse and returns rows formatted as a JSON string.
    Only SELECT queries are authorized.
    """
    # Clean up any potential markdown formatting syntax applied by the LLM client
    query = sql_query.strip().replace("```sql", "").replace("```", "").strip()
    
    # --- MANDATORY SECURITY GUARDRAIL ---
    # Intercept and block any mutation attempts (DROP, DELETE, UPDATE, INSERT, ALTER, etc.)
    forbidden_keywords = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "merge"]
    query_lower = query.lower()
    
    if any(keyword in query_lower for keyword in forbidden_keywords) or not query_lower.startswith("select"):
        return "Security Violation Error: Only read-only SELECT queries are authorized on this endpoint."
        
    try:
        # Call the unified Cloudera Impala client helper
        raw_result = execute_query(query)
        
        # Extract rows (list of dicts) to preserve exact compatibility with downstream parsers
        records = raw_result.get("rows", [])
        
        # Return the records as a standardized JSON string payload
        return json.dumps(records, default=str)
            
    except Exception as e:
        return f"Cloudera Impala Engine Error: {str(e)}"
    
def get_database_schema() -> str:
    """
    Safely locates and reads the master domain configuration blueprint 
    using absolute system routing paths to bypass container directory shifts.
    """
    # 🔒 Absolute enterprise path matching your repository layout
    primary_production_path = "/home/cdsw/ask-data/backend/domain_config.yaml"
    local_development_fallback = "../backend/domain_config.yaml"
    
    # Choose whichever path actively exists in the current container context
    target_path = primary_production_path if os.path.exists(primary_production_path) else local_development_fallback
    
    try:
        with open(target_path, "r", encoding="utf-8") as file:
            schema_content = file.read().strip()
            
        if not schema_content:
            return "Error: The domain_config.yaml file was found but it is completely empty."
            
        return schema_content
        
    except Exception as e:
        # Returns a detailed tracking message to identify the failure point immediately
        return f"Error: Enterprise configuration mapping file could not be read at {target_path}. System Details: {str(e)}"