import os
import sys
import subprocess

if '__file__' in locals():
    script_dir = os.path.dirname(os.path.abspath(__file__))
else:
    # Pointing strictly to your active mcp_server repository folder
    cml_default_mcp = "/home/cdsw/ask-data/mcp_server"
    script_dir = cml_default_mcp if os.path.exists(cml_default_mcp) else os.getcwd()
    
os.chdir(script_dir)
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

def install_dependencies():
    """Automatically installs packages from requirements.txt on startup"""
    requirements_path = "requirements.txt"
    if os.path.exists(requirements_path):
        print("📦 Found requirements.txt. Ensuring all server dependencies are installed...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        print("✅ Dependencies up to date.")
    else:
        print("⚠️ Warning: requirements.txt not found in current directory.")

# Self-heal your environment dependencies first
install_dependencies()

# Core framework components
import uvicorn
from fastapi import FastAPI, Request
from starlette.routing import Mount
from fastmcp import FastMCP
from mcp.server.sse import SseServerTransport

# 1. Initialize the central FastMCP application state
mcp = FastMCP("Bank-ABC-Modular-Orchestrator")

# 2. Configure the standardized SSE message pipeline transport
sse = SseServerTransport("/messages")

# --- ACTIVE TOOL REGISTRATION ---
# Dynamically register your standalone tool function into the FastMCP instance
from app.tools.sql_query import execute_banking_query

# Dynamically register your schema mapping tool into the FastMCP instance
from app.tools.sql_query import get_database_schema

@mcp.tool(name="get_database_schema")
def mcp_get_database_schema() -> str:
    """
    Retrieves the structural enterprise schema configuration, table layouts, 
    available columns, column types, primary/foreign keys, and data relationships.
    """
    return get_database_schema()

@mcp.tool(name="execute_banking_query")
def mcp_execute_banking_query(sql_query: str) -> str:
    """
    Executes a read-only MySQL SELECT statement against the live bank analytics database 
    through the secure tunnel and returns rows as a formatted JSON string.
    """
    return execute_banking_query(sql_query)

# Dynamically register your unstructured RAG search engine into the FastMCP instance
from app.tools.rag_search import perform_rag_search

@mcp.tool(name="search_policy_knowledge_base")
def mcp_search_policy_knowledge_base(query: str) -> str:
    """
    Scans through internal unstructured enterprise banking policies, compliance guidelines, 
    and SOP documents to return relevant textual contextual snippets for a given query.
    """
    return perform_rag_search(query)

# Dynamically register your specialized risk analytics engine into the FastMCP instance
from app.tools.dormant_risk import calculate_dormant_account_risk

@mcp.tool(name="evaluate_dormant_account_risk")
def mcp_evaluate_dormant_account_risk(days_inactive: int, account_balance: float, sudden_withdrawal_amount: float = 0.0) -> str:
    """
    Calculates a risk priority score, classification tier, and security intervention flags 
    for an inactive bank account using internal compliance risk matrix rules.
    """
    return calculate_dormant_account_risk(days_inactive, account_balance, sudden_withdrawal_amount)


# 3. Create the FastAPI container to manage incoming enterprise cluster traffic
app = FastAPI(title="Bank ABC Production MCP Gateway")

# Route incoming protocol control packets cleanly into the SSE transport layer
app.router.routes.append(Mount("/messages", app=sse.handle_post_message))


@app.get("/health")
def platform_health_check():
    """Basic endpoint used by Cloudera AI to verify the container layer is active"""
    return {
        "status": "healthy", 
        "protocol": "Model Context Protocol v1", 
        "transport": "Server-Sent Events (SSE)"
    }


@app.get("/sse")
async def handle_sse_handshake(request: Request):
    """Establishes the long-lived protocol connection stream for incoming AI clients"""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp._mcp_server.run(
            streams[0], streams[1], mcp._mcp_server.create_initialization_options()
        )

# =====================================================================
# 🧪 SWAGGER DOCS INTERACTIVE TESTING ENDPOINTS
# =====================================================================

@app.get("/api/test/schema")
def test_schema_tool():
    """Interactive playground to test your get_database_schema tool"""
    from app.tools.sql_query import get_database_schema
    return {"raw_yaml_configuration": get_database_schema()}

@app.post("/api/test/sql")
def test_sql_tool(mysql_query: str):
    """Interactive playground to test your execute_banking_query tool"""
    from app.tools.sql_query import execute_banking_query
    import json
    raw_result = execute_banking_query(mysql_query)
    try:
        # Try to parse it into clean JSON if it's database rows
        return {"status": "success", "data": json.loads(raw_result)}
    except:
        # Return as raw text if it's an error message or string guardrail
        return {"status": "info_or_error", "message": raw_result}

@app.post("/api/test/rag")
def test_rag_tool(search_query: str):
    """Interactive playground to test your search_policy_knowledge_base tool"""
    from app.tools.rag_search import perform_rag_search
    return {"status": "success", "matched_context": perform_rag_search(search_query)}

if __name__ == "__main__":
    # Follow the dedicated application port assigned by Cloudera AI
    app_port = int(os.getenv("CDSW_APP_PORT", 8090))
    
    print(f"🌐 Launching Production MCP Server on http://localhost:{app_port}")
    print(f"📡 Serving protocol streams on http://localhost:{app_port}/sse")
    
    uvicorn.run(
        app, 
        host="localhost",  # 🔒 Locked strictly to localhost per enterprise guidelines
        port=app_port, 
        log_level="info"
    )