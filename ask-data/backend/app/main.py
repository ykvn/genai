import os
import json
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.schemas.query import QueryRequest
from app.services.translator import SQLTranslationService

# --- NEW: Model Context Protocol Protocol Ecosystem imports ---
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount

app = FastAPI(title="Bank ABC NL-to-SQL Core API")
translator_service = SQLTranslationService()

# 1. Initialize the official FastMCP Server Interface
mcp = FastMCP("Bank-ABC-Analytics-Engine")
sse = SseServerTransport("/messages")


# =====================================================================
# 🛠️ MCP TOOL LAYERS (Exposed directly to compliant AI Clients)
# =====================================================================

@mcp.tool()
def get_database_schema() -> str:
    """
    Retrieves the structural enterprise schema configuration, table layouts, 
    available columns, column types, primary/foreign keys, and data relationships.
    """
    # Dynamically maps back to your existing domain config file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "domain_config.yaml")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return f.read()
        return "Error: Enterprise configuration mapping file not found."
    except Exception as e:
        return f"Failed to parse domain metadata context: {str(e)}"


@mcp.tool()
def execute_banking_query(sql_query: str) -> str:
    """
    Executes a read-only MySQL SELECT statement against the live bank analytics database 
    through the secure tunnel and returns rows as formatted JSON text.
    Only SELECT queries are authorized.
    """
    # Clean up markdown formatting blocks if added by the LLM client
    query = sql_query.strip().replace("```sql", "").replace("```", "").strip()
    
    # Direct security guardrail check
    if not query.lower().startswith("select"):
        return "Security Violation: Non-SELECT mutations are strictly blocked."
        
    db = SessionLocal()
    try:
        db_result = db.execute(text(query))
        records = [dict(row) for row in db_result.mappings()]
        return json.dumps(records, default=str)
    except Exception as e:
        return f"Database Execution Error: {str(e)}"
    finally:
        db.close()


# =====================================================================
# 🌐 PRESERVED ORIGINAL HTTP ENDPOINTS (Kept intact for backwards compatibility)
# =====================================================================

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
        
        # 2. Execute the query directly on your home MySQL server via誠SQLAlchemy
        db_result = db.execute(text(generated_sql))
        
        # 3. Convert the database rows into a list of dictionaries
        records = [dict(row) for row in db_result.mappings()]
        
        return {
            "question": user_question,
            "status": "Success",
            "predicted_sql": generated_sql,
            "row_count": len(records),
            "data": records 
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database Execution Failure: {str(e)}"
        )


# =====================================================================
# 🔌 MCP TRANSPORT LOOPBACK LAYER MOUNTS
# =====================================================================

# Append the message handling Mount directly to the primary router table
app.router.routes.append(Mount("/messages", app=sse.handle_post_message))


@app.get("/sse")
async def handle_sse(request: Request):
    """Establishes the long-lived SSE connection stream for incoming protocol clients"""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp._mcp_server.run(
            streams[0], streams[1], mcp._mcp_server.create_initialization_options()
        )