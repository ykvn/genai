import sys
from fastapi import FastAPI, HTTPException

# 🩹 ENTERPRISE RUNTIME PATCH: Force modern SQLite layers immediately!
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from app.schemas.query import QueryRequest
from app.services.translator import SQLTranslationService

app = FastAPI(title="Bank ABC NL-to-SQL Core API Gateway")
translator_service = SQLTranslationService()


def is_policy_question(question: str) -> bool:
    """Heuristic Intent Classifier: Evaluates keywords to route to RAG vs SQL."""
    q_lower = question.lower()
    rag_keywords = [
        "kebijakan", "sop", "prosedur", "manual", "panduan", "kriteria", 
        "aturan", "regulasi", "dokumen", "syarat", "sk", "surat keputusan"
    ]
    return any(keyword in q_lower for keyword in rag_keywords)


# =====================================================================
# 🌐 UNIFIED HEALTH CHECKS & HTTP ENDPOINTS
# =====================================================================

@app.get("/")
@app.get("/health")
def health_check():
    """Satisfies platform container health checks."""
    return {"status": "healthy", "gateway": "operational"}


@app.post("/ask")
def ask_ai(payload: QueryRequest):
    """Processes natural language questions and routes them appropriately."""
    try:
        user_question = payload.question
        
        # 📑 PATH B: Document / Policy / SOP Intent Detected (ChromaDB RAG)
        if is_policy_question(user_question):
            print("📚 Policy Inquiry Intercepted. Triggering RAG Strategy...")
            rag_answer = translator_service.generate_rag_answer(user_question)
            
            return {
                "question": user_question,
                "status": "Success",
                "type": "RAG",
                "predicted_sql": None,
                "row_count": 0,
                "data": [],
                "response": rag_answer
            }
        
        # 📊 PATH A: Analytical Data / Metrics Intent Detected (Impala Text-to-SQL)
        else:
            print("📊 Analytical Query Intercepted. Initializing Agent Loop...")
            generated_sql = translator_service.generate_sql(user_question)
            
            # Programmatic intercept if the security guardrail gets tripped by CrewAI
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
            
            # 🔌 THE FIX: Fetch records entirely via the MCP server protocol stream!
            records = translator_service.run_mcp_query(generated_sql)
            
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
            detail=f"Gateway Processing Failure: {str(e)}"
        )