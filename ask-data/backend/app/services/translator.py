import os
import sys
import json
import asyncio
from pathlib import Path

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

# 🔌 Official Model Context Protocol Client Packages
from mcp import ClientSession
from mcp.client.sse import sse_client

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

    async def _fetch_schema_via_mcp(self) -> str:
        """
        NATIVE MCP CLIENT ROUTINE: Connects directly to the universal /sse channel, 
        initializes a session, and calls the schema tool over the standardized protocol.
        """
        sse_endpoint = f"{self.mcp_server_url.rstrip('/')}/sse"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            # Connect natively to the universal protocol stream channel
            async with sse_client(url=sse_endpoint, headers=headers) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    # Perform official protocol initialization handshake
                    await session.initialize()
                    
                    # Call the tool directly by its registered name payload
                    result = await session.call_tool("get_database_schema")
                    
                    # Extract contents cleanly without manual JSON parsing keys
                    if result and result.content:
                        return result.content[0].text
                    return "Error: Empty schema content returned from protocol channel."
        except Exception as e:
            print(f"⚠️ Native MCP Protocol fetch failed: {str(e)}")
            return "Error: Unable to load structural layout matrix via protocol stream."

    async def _execute_query_via_mcp(self, sql_query: str) -> str:
        """
        NATIVE MCP CLIENT ROUTINE: Connects to the /sse channel, initializes 
        a session, and executes the generated query via the MCP execution tool.
        """
        sse_endpoint = f"{self.mcp_server_url.rstrip('/')}/sse"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with sse_client(url=sse_endpoint, headers=headers) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    
                    # Call the execution tool, passing the SQL string as a parameter
                    result = await session.call_tool(
                        "execute_banking_query", 
                        arguments={"sql_query": sql_query}
                    )
                    
                    if result and result.content:
                        return result.content[0].text
                    return "[]"
        except Exception as e:
            print(f"⚠️ Native MCP Query execution failed: {str(e)}")
            return json.dumps([{"error": f"MCP Transmission Failure: {str(e)}"}])

    def run_mcp_query(self, sql_query: str) -> list:
        """Synchronous wrapper to execute the query and parse the JSON response."""
        raw_json = asyncio.run(self._execute_query_via_mcp(sql_query))
        try:
            return json.loads(raw_json)
        except Exception:
            # Fallback if the server returned a plain string error message
            return [{"execution_message": raw_json}]

    # =========================================================================
    # 📑 PATH A: OPTIMIZED TEXT-TO-SQL ENGINE (DIRECT CONTEXT INJECTION)
    # =========================================================================
    def generate_sql(self, user_question: str) -> str:
        """Deterministic execution pipeline that forces schema adherence for compact models."""
        
        # 1. Authentic protocol tool execution call via asyncio event loop execution bridges
        print("📡 Fetching database schema layout natively over MCP protocol streams...")
        db_schema_layout = asyncio.run(self._fetch_schema_via_mcp())

        # 2. Define the structural engineering persona (Cleaned of tool overhead)
        sql_developer = Agent(
            role="Senior Cloudera Impala Analytics Architect",
            goal="Convert conversational user requests into valid, highly optimized read-only Impala SQL statements.",
            backstory=(
                "You are an expert big data analytics engineer at Bank Jatim specializing in Cloudera SDX environments. "
                "You strictly write queries compatible with the Cloudera Impala engine, using standard ANSI/Hive SQL syntax "
                "and adhering exactly to the provided table structures."
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
                "4. CRITICAL SECURITY GUARDRAIL: If you detect mutation or administrative attempts "
                "(INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT), "
                "abort operations immediately and return exactly this block:\n"
                "```sql\nSELECT 'CRITICAL_SECURITY_ALERT: Unauthorized Command Blocked' AS security_status;\n```"
            ),
            expected_output="A clean Cloudera Impala SELECT statement inside a standard markdown code block wrapper based strictly on the provided layout text.",
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