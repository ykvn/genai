import os
import json
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.schemas.query import QueryRequest
from app.services.translator import SQLTranslationService

# --- Model Context Protocol Ecosystem imports ---
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.routing import Mount

app = FastAPI(title="Bank ABC NL-to-SQL Core API")
translator_service = SQLTranslationService()

# Initialize the official FastMCP Server Interface
mcp = FastMCP("Bank-ABC-Analytics-Engine")
sse = SseServerTransport("/messages")


def is_policy_question(question: str) -> bool:
    """
    Heuristic Intent Classifier: Evaluates keywords to determine whether a query
    is a document/policy request (RAG) or an analytical database request (SQL).
    """
    q_lower = question.lower()
    # Comprehensive routing keywords matching your deployment manual guidelines
    rag_keywords = [
        "kebijakan", "sop", "prosedur", "manual", "panduan", "kriteria", 
        "aturan", "regulasi", "dokumen", "syarat", "sk", "surat keputusan"
    ]
    return any(keyword in q_lower for keyword in rag_keywords)


# =====================================================================
# 🛠️ MCP TOOL LAYERS (Exposed directly to compliant AI Clients)
# =====================================================================

@mcp.tool()
def get_database_schema() -> str:
    """
    Retrieves the structural enterprise schema configuration, table layouts, 
    available columns, column types, primary/foreign keys, and data relationships.
    """
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
    query = sql_query.strip().replace("```sql", "").replace("```", "").strip()
    
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


@mcp.tool()
def search_policy_documents(query: str) -> str:
    """
    Performs a semantic vector distance search against local persistent enterprise manuals 
    and policy documentation (ChromaDB) to return matching structural context fragments.
    """
    try:
        context_fragments = translator_service.retrieve_relevant_documents(query, top_k=2)
        return context_fragments
    except Exception as e:
        return f"Knowledge Base Vector Retrieval Failure: {str(e)}"


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
    Processes natural language questions, automatically splits routing lines 
    between document policies (RAG) and relational transactions (SQL), 
    and handles output payload assembly.
    """
    try:
        user_question = payload.question
        
        # 📑 PATH B: Document / Policy / SOP Intent Detected
        if is_policy_question(user_question):
            print(f"📚 Policy Inquiry Intercepted. Triggering Local Vector Store Retrieval Strategy...")
            rag_answer = translator_service.generate_rag_answer(user_question)
            
            return {
                "question": user_question,
                "status": "Success",
                "type": "RAG",
                "predicted_sql": None,
                "row_count": 0,
                "data": [],
                "response": rag_answer  # Next.js UI captures this field directly for rendering text markup
            }
        
        # 📊 PATH A: Analytical Data / Metrics Intent Detected
        else:
            print(f"📊 Analytical Query Intercepted. Initializing Agent Loop Processing Routine...")
            generated_sql = translator_service.generate_sql(user_question)
            
            # Strict programmatic intercept if the translator's security guardrail gets tripped
            if "CRITICAL_SECURITY_ALERT" in generated_sql:
                return {
                    "question": user_question,
                    "status": "Blocked",
                    "type": "SQL",
                    "predicted_sql": generated_sql,
                    "row_count": 0,
                    "data": [],
                    "response": "Security Violation: This destructive request was terminated by system guardrails."
                }
            
            # Execute the verified, read-only SQL query against your SQLAlchemy pool connection
            db_result = db.execute(text(generated_sql))
            records = [dict(row) for row in db_result.mappings()]
            
            return {
                "question": user_question,
                "status": "Success",
                "type": "SQL",
                "predicted_sql": generated_sql,
                "row_count": len(records),
                "data": records,
                "response": None
            }
        
    except Exception as e:
        print(f"❌ Core API Router Processing Failure: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Database Execution Failure: {str(e)}"
        )


# =====================================================================
# 🔌 MCP TRANSPORT LOOPBACK LAYER MOUNTS
# =====================================================================

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