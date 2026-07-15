import os
import json
import urllib.request
import time

# 🩹 ENTERPRISE LINUX RUNTIME PATCH: Force modern SQLite layers before importing ChromaDB
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import chromadb
from sentence_transformers import SentenceTransformer

# 🤖 CrewAI Framework Engine Integration Modules
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

class SQLTranslationService:
    def __init__(self):
        # 🌐 Microservice network endpoints preserved from your architectural rules
        self.mcp_server_url = os.getenv("MCP_SERVER_URL")[cite: 1]
        
        # 🔌 LiteLLM Connection Point: Extract the CML App Subdomain path assigned to LiteLLM
        # CrewAI manages the completions endpoint strings internally; pass the base URL directory path
        self.qwen_base_url = os.getenv("QWEN_BASE_URL", "http://localhost:8100/v1").rstrip("/")[cite: 1]
        
        # 🔑 Security Access Handshake Tokens
        self.api_token = os.getenv("CML_TOKEN") or os.getenv("QWEN_API_KEY") or "litellm-dummy-token"[cite: 1]

        # 🧠 Initialize the CrewAI Native LLM Interface pointing directly to your LiteLLM Proxy
        print(f"📡 Connecting CrewAI to Standalone LiteLLM Proxy Gateway at: {self.qwen_base_url}")
        self.llm = LLM(
            model=f"openai/{os.getenv('QWEN_MODEL', 'qwen2.5-3b-instruct')}",[cite: 1]
            base_url=self.qwen_base_url,
            api_key=self.api_token,
            temperature=0.0
        )

        # 📚 Vector DB Configuration Keys (Path B / RAG)
        self.chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "/home/cdsw/ask-data/backend/chroma_db")[cite: 1]
        self.collection_name = os.getenv("CHROMA_COLLECTION", "bank_jatim_knowledge")[cite: 1]
        
        # 🧠 Initialize local embedding model directly on the vCPU allocation
        print("🧠 Loading local MiniLM-L6 vector embedding weights...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")[cite: 1]
        
        # Connect to the persistent Chroma storage directory
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)[cite: 1]
        self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)[cite: 1]

    # =========================================================================
    # 📑 PATH A: UPGRADED CREWAI TEXT-TO-SQL AGENT ENGINE
    # =========================================================================
    def generate_sql(self, user_question: str) -> str:
        """Autonomous execution loop replacing the legacy manual turn code structures."""
        
        # Define a standalone tool context that CrewAI can execute dynamically
        @tool("Fetch Database Schema Layout")
        def fetch_schema_tool() -> str:
            """Useful when you need to inspect table names, available columns, primary keys, 
            and data relationships from the MySQL cluster layout before drafting a query."""
            target_mcp_endpoint = f"{os.getenv('MCP_SERVER_URL')}/api/test/schema"[cite: 1]
            token = os.getenv("CML_TOKEN") or os.getenv("QWEN_API_KEY") or ""[cite: 1]
            try:
                req = urllib.request.Request(
                    target_mcp_endpoint,
                    headers={"Authorization": f"Bearer {token}"},[cite: 1]
                    method="GET"
                )
                with urllib.request.urlopen(req, timeout=10) as response:[cite: 1]
                    schema_data = json.loads(response.read().decode("utf-8"))[cite: 1]
                    return schema_data.get("raw_yaml_configuration", "")[cite: 1]
            except Exception as e:
                return f"Failed to reach target schema configuration gateway: {str(e)}"

        # 1. Define the structural engineering persona
        sql_developer = Agent(
            role="Senior MySQL 8.0 Database Translation Architect",
            goal="Convert conversational user requests into valid, optimized read-only SQL statements.",
            backstory=(
                "You are an expert analytics engineer at Bank Jatim. You strictly examine structural "
                "table schema definitions using your tool options before declaring a final statement code asset."
            ),
            tools=[fetch_schema_tool],
            llm=self.llm,
            verbose=True
        )

        # 2. Declare the rigorous task boundaries to match your enterprise safety mandates
        draft_sql_task = Task(
            description=(
                f"Process the following user query: '{user_question}'.\n"
                "OPERATIONAL BOUNDARIES:\n"
                "1. You MUST request the system table schemas first using your available tools.\n"
                "2. Once schema details are parsed, output your query wrapped inside a clean markdown ```sql ``` block.\n"
                "3. CRITICAL SECURITY GUARDRAIL: If you detect mutation attempts (INSERT, UPDATE, DELETE, DROP), "
                "abort operations immediately and return exactly this block:\n"
                "```sql\nSELECT 'CRITICAL_SECURITY_ALERT: Unauthorized Command Blocked' AS security_status;\n```"
            ),
            expected_output="A clean MySQL SELECT statement inside a standard markdown code block wrapper.",
            agent=sql_developer
        )

        # 3. Assemble and launch the automated agent team context
        orchestration_crew = Crew(
            agents=[sql_developer],
            tasks=[draft_sql_task],
            process=Process.sequential
        )

        print("⏳ Initiating autonomous CrewAI execution pipeline via LiteLLM application layer...")
        ai_result = str(orchestration_crew.kickoff()).strip()

        # Extract the pure query string from the markdown blocks for downstream execution compatibility
        if "```sql" in ai_result:[cite: 1]
            return ai_result.split("```sql")[1].split("```")[0].strip()[cite: 1]
        elif "SELECT" in ai_result.upper():[cite: 1]
            return ai_result.replace("```", "").strip()[cite: 1]
        
        return ai_result[cite: 1]

    # =========================================================================
    # 📑 PATH B: KNOWLEDGE BASE VECTOR RETRIEVAL (RAG)
    # =========================================================================
    def retrieve_relevant_documents(self, query: str, top_k: int = 5) -> str:
        """Runs semantic vector extraction against local persistent database storage."""
        if self.collection.count() == 0:[cite: 1]
            return "No document metadata registered in Knowledge Base storage."[cite: 1]

        query_vector = self.embedding_model.encode(query).tolist()[cite: 1]
        
        results = self.collection.query([cite: 1]
            query_embeddings=[query_vector],[cite: 1]
            n_results=top_k[cite: 1]
        )
        
        retrieved_contexts = []
        if results and 'documents' in results and results['documents']:[cite: 1]
            for idx, text in enumerate(results['documents'][0]):[cite: 1]
                source = results['metadatas'][0][idx]['source_file'][cite: 1]
                retrieved_contexts.append(f"[Source Manual: {source}]\n{text}")[cite: 1]
                
        return "\n\n---\n\n".join(retrieved_contexts)[cite: 1]

    def generate_rag_answer(self, user_question: str) -> str:
        """Coordinates unstructured context parsing with Qwen via LiteLLM to answer policies."""
        document_context = self.retrieve_relevant_documents(user_question, top_k=5)[cite: 1]
        
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