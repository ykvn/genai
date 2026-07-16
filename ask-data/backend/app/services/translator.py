import os
import sys
import json
import urllib.request

# 🩹 ENTERPRISE LINUX RUNTIME PATCH: Force modern SQLite layers before importing ChromaDB
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import chromadb
from sentence_transformers import SentenceTransformer

# 🤖 CrewAI Framework Engine Integration Modules
from crewai import Agent, Task, Crew, Process, LLM

class SQLTranslationService:
    def __init__(self):
        # 🌐 Microservice network endpoints preserved from architectural rules
        self.mcp_server_url = os.getenv("MCP_SERVER_URL")
        
        # 🔌 LiteLLM Connection Point: Point strictly to loopback interface mapping targets
        self.qwen_base_url = os.getenv("QWEN_BASE_URL").rstrip("/")
        
        # 🔑 Security Access Handshake Tokens
        self.api_token = os.getenv("CML_TOKEN") or os.getenv("QWEN_API_KEY") or "litellm-dummy-token"

        # 🧠 Initialize the CrewAI Native LLM Interface pointing directly to your LiteLLM Proxy
        print(f"📡 Connecting CrewAI to Standalone LiteLLM Proxy Gateway at: {self.qwen_base_url}")
        self.llm = LLM(
            model=f"openai/{os.getenv('QWEN_MODEL', 'qwen2.5-3b-instruct')}",
            base_url=self.qwen_base_url,
            api_key=self.api_token,
            temperature=0.0
        )

        # 📚 Vector DB Configuration Keys (Path B / RAG)
        self.chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "/home/cdsw/ask-data/backend/chroma_db")
        self.collection_name = os.getenv("CHROMA_COLLECTION", "bank_jatim_knowledge")
        
        # 🧠 Initialize local embedding model directly on the vCPU allocation
        print("🧠 Loading local MiniLM-L6 vector embedding weights...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Connect to the persistent Chroma storage directory
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)

    # =========================================================================
    # 📑 PATH A: OPTIMIZED TEXT-TO-SQL ENGINE (DIRECT CONTEXT INJECTION)
    # =========================================================================
    def generate_sql(self, user_question: str) -> str:
        """Deterministic execution pipeline that forces schema adherence for compact models."""
        
        # 1. Force Python to fetch the schema directly from the MCP Server upfront
        print("📡 Fetching database schema layout from MCP cluster network...")
        target_mcp_endpoint = f"{self.mcp_server_url}/api/test/schema"
        try:
            req = urllib.request.Request(
                target_mcp_endpoint,
                headers={"Authorization": f"Bearer {self.api_token}"},
                method="GET"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                schema_data = json.loads(response.read().decode("utf-8"))
                db_schema_layout = schema_data.get("raw_yaml_configuration", "")
        except Exception as e:
            print(f"⚠️ Schema fetch fallback triggered: {str(e)}")
            db_schema_layout = "Error: Unable to load structural layout matrix."

        # 2. Define the structural engineering persona (Cleaned of tool overhead)
        sql_developer = Agent(
            role="Senior MySQL 8.0 Database Translation Architect",
            goal="Convert conversational user requests into valid, optimized read-only SQL statements.",
            backstory=(
                "You are an expert analytics engineer at Bank Jatim. You strictly write queries "
                "using only the exact table structures, explicit columns, and data relationships provided to you."
            ),
            llm=self.llm,
            verbose=True
        )

        # 3. Inject the schema layout directly into the Task description text
        draft_sql_task = Task(
            description=(
                f"Process the following user query: '{user_question}'.\n\n"
                f"📊 VERIFIED LIVE DATABASE SCHEMA LAYOUT:\n"
                f"{db_schema_layout}\n\n"
                "OPERATIONAL BOUNDARIES:\n"
                "1. CRITICAL: You MUST strictly use the actual table and column names listed in the LIVE DATABASE SCHEMA LAYOUT above.\n"
                "2. DO NOT guess, assume, or invent generic tables (such as 'customer' or 'users') if they are not explicitly declared in the schema layout above.\n"
                "3. Output your query wrapped inside a clean markdown ```sql ``` block.\n"
                "4. CRITICAL SECURITY GUARDRAIL: If you detect mutation attempts (INSERT, UPDATE, DELETE, DROP), "
                "abort operations immediately and return exactly this block:\n"
                "```sql\nSELECT 'CRITICAL_SECURITY_ALERT: Unauthorized Command Blocked' AS security_status;\n```"
            ),
            expected_output="A clean MySQL SELECT statement inside a standard markdown code block wrapper based strictly on the provided layout text.",
            agent=sql_developer
        )

        # 4. Assemble and launch the automated agent team context
        orchestration_crew = Crew(
            agents=[sql_developer],
            tasks=[draft_sql_task],
            process=Process.sequential
        )

        print("⏳ Initiating autonomous CrewAI execution pipeline via LiteLLM application layer...")
        ai_result = str(orchestration_crew.kickoff()).strip()

        # Extract the pure query string from the markdown blocks for downstream execution compatibility
        if "```sql" in ai_result:
            return ai_result.split("```sql")[1].split("```")[0].strip()
        elif "SELECT" in ai_result.upper():
            return ai_result.replace("```", "").strip()
        
        return ai_result

    # =========================================================================
    # 📑 PATH B: KNOWLEDGE BASE VECTOR RETRIEVAL (RAG)
    # =========================================================================
    def retrieve_relevant_documents(self, query: str, top_k: int = 5) -> str:
        """Runs semantic vector extraction against local persistent database storage."""
        if self.collection.count() == 0:
            return "No document metadata registered in Knowledge Base storage."

        query_vector = self.embedding_model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        
        retrieved_contexts = []
        if results and 'documents' in results and results['documents']:
            for idx, text in enumerate(results['documents'][0]):
                source = results['metadatas'][0][idx]['source_file']
                retrieved_contexts.append(f"[Source Manual: {source}]\n{text}")
                
        return "\n\n---\n\n".join(retrieved_contexts)

    def generate_rag_answer(self, user_question: str) -> str:
        """Coordinates unstructured context parsing with Qwen via LiteLLM to answer policies."""
        document_context = self.retrieve_relevant_documents(user_question, top_k=5)
        
        compliance_officer = Agent(
            role="Authoritative Corporate Policy Compliance Specialist",
            goal="Formulate high-fidelity textual responses based exclusively on provided manuals.",
            backstory="You represent the internal policy audit team. You match facts exactly and never speculate.",
            llm=self.llm,
            verbose=True
        )

        evaluate_policy_task = Task(
            description=(
                f"Review the following corporate reference manuals carefully:\n\n"
                f"VERIFIED CONTEXT:\n{document_context}\n\n"
                f"USER QUESTION: {user_question}\n\n"
                f"MANDATE: Rely strictly on the reference text above. If details cannot be derived, "
                f"state clearly that you do not possess that information. Do not hallucinate facts."
            ),
            expected_output="A perfectly formatted conversational text response ready for UI display.",
            agent=compliance_officer
        )

        rag_crew = Crew(
            agents=[compliance_officer],
            tasks=[evaluate_policy_task]
        )

        return str(rag_crew.kickoff()).strip()