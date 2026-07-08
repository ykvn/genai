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

class SQLTranslationService:
    def __init__(self):
        # 🌐 Microservice network endpoints 
        self.mcp_server_url = os.getenv("MCP_SERVER_URL")
        
        # Robust URL fallback to match your environment guides
        qwen_base = os.getenv("QWEN_BASE_URL", "").rstrip("/")
        self.qwen_engine_url = os.getenv(
            "QWEN_LLM_URL", 
            f"{qwen_base}/chat/completions" if qwen_base else None
        )
        
        # 🔑 Security Access Handshake Tokens
        self.api_token = os.getenv("CML_TOKEN") or os.getenv("QWEN_API_KEY")

        # 📚 Vector DB Configuration Keys (Path A / RAG)
        self.chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "/home/cdsw/ask-data/backend/chroma_db")
        self.collection_name = os.getenv("CHROMA_COLLECTION", "bank_jatim_knowledge")
        
        # 🧠 Initialize local embedding model directly on the 4 vCPU allocation
        print("🧠 Loading local MiniLM-L6 vector embedding weights...")
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Connect to the persistent Chroma storage directory
        self.chroma_client = chromadb.PersistentClient(path=self.chroma_dir)
        self.collection = self.chroma_client.get_or_create_collection(name=self.collection_name)

    # =========================================================================
    # 📑 PATH A: PURE MCP TEXT-TO-SQL AGENT LOOP
    # =========================================================================
    def generate_sql(self, user_question: str) -> str:
        if not self.api_token:
            raise RuntimeError("CRITICAL: 'CML_TOKEN' environment variable is missing on the Backend Application.")
        if not self.qwen_engine_url:
            raise RuntimeError("CRITICAL: Qwen Engine endpoint address configurations are missing.")

        agent_system_prompt = """You are an advanced text-to-SQL translation agent for a MySQL 8.0 database.

You have access to an internal Model Context Protocol (MCP) tool to read the schema definitions from disk. 

AVAILABLE TOOLS:
- `get_schema` : Retrieves table schemas, columns, primary keys, and data relationships.

OPERATIONAL PROTOCOL:
1. If the database schema has NOT been provided to you yet in the conversation history, you are strictly forbidden from writing a final SQL statement. You MUST request the schema first by outputting exactly:
   CALL: get_schema()
2. Once the schema data is provided to you as a TOOL_RESPONSE in the next turn, analyze the columns carefully and output your final answer inside a standard markdown ```sql ``` block. Do not provide conversational explanations outside the code block.

FEW-SHOT WORKFLOW EXAMPLES:

Example of Turn 1 (Initial Request):
User: show active customer
Assistant: CALL: get_schema()

Example of Turn 2 (Accurate Join Execution):
User: TOOL_RESPONSE (get_schema): [schema text showing table 'customers' with no status column, and table 'savings' with a status column matching 'ACTIVE']
Assistant: ```sql
SELECT c.customer_id, c.first_name, c.last_name, c.email 
FROM customers c 
INNER JOIN savings s ON c.customer_id = s.customer_id 
WHERE s.status = 'ACTIVE' 
LIMIT 100;

CRITICAL SAFETY BOUNDARIES:
- You are strictly forbidden from writing INSERT, UPDATE, DELETE, or DROP commands.
- If a user requests a forbidden command (like deleting data or dropping tables), you MUST immediately abort your protocol and output exactly this dummy safety statement inside your markdown wrapper:
```sql
SELECT 'CRITICAL_SECURITY_ALERT: Unauthorized Command Blocked' AS security_status;
``` """

        # Enforce isolated, state-free conversation tracking
        messages = [
            {"role": "system", "content": agent_system_prompt},
            {"role": "user", "content": user_question}
        ]

        for turn in range(3):
            payload = {
                "model": os.getenv("QWEN_MODEL", "qwen2.5-3b-instruct"),
                "messages": messages, 
                "temperature": 0.0
            }

            print(f"⏳ [AGENT ROUTER - Turn {turn + 1}] Packing conversation payload and executing Qwen completion phase...")
            try:
                req = urllib.request.Request(
                    self.qwen_engine_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_token}"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=90) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    ai_response = result["choices"][0]["message"]["content"].strip()
            except Exception as e:
                raise RuntimeError(f"Failed to communicate with Qwen Engine App: {str(e)}")

            print(f"🤖 [AGENT ROUTER - Turn {turn + 1}] Captured Raw Qwen Model Output:\n{ai_response}\n")

            # 🛠️ HIGH-VISIBILITY MCP ROUTING LOGS INJECTED HERE
            if "get_schema" in ai_response.lower():
                target_mcp_endpoint = f"{self.mcp_server_url}/api/test/schema"
                
                print("=====================================================================")
                print("📡  MCP TOOL INVOCATION DETECTED!")
                print(f"🔗  Routing Target URL : {target_mcp_endpoint}")
                print(f"🔑  Authorization Auth  : Bearer {self.api_token[:10]}...[REDACTED]")
                print("=====================================================================")
                
                try:
                    schema_req = urllib.request.Request(
                        target_mcp_endpoint,
                        headers={"Authorization": f"Bearer {self.api_token}"},
                        method="GET"
                    )
                    
                    start_time = time.time()
                    with urllib.request.urlopen(schema_req, timeout=5) as schema_resp:
                        schema_data = json.loads(schema_resp.read().decode("utf-8"))
                        schema_context = schema_data.get("raw_yaml_configuration", "")
                    elapsed_time = time.time() - start_time
                    
                    print(f"✅  MCP RESPONSE RECEIVED SUCCESSFULLY ({elapsed_time:.2f}s)")
                    print(f"📦  Payload Metrics: Extracted {len(schema_context)} characters of raw structural YAML schema context.")
                    print("=====================================================================\n")
                    
                except Exception as e:
                    print("❌  CRITICAL MCP ROUTING FAILURE!")
                    print(f"💥  Failed Connection Attempt to Endpoint: {target_mcp_endpoint}")
                    print(f"📝  Network Error Trace: {str(e)}")
                    print("=====================================================================\n")
                    raise RuntimeError(f"MCP Tool Server communication failed: {str(e)}")

                messages.append({"role": "assistant", "content": ai_response})
                messages.append({
                    "role": "user", 
                    "content": f"TOOL_RESPONSE (get_schema):\n{schema_context}\n\nReview this schema and execute Step 2 and Step 3 of your protocol."
                })
                continue

            # Extract the pure query string from the markdown blocks
            if "```sql" in ai_response:
                generated_sql = ai_response.split("```sql")[1].split("```")[0].strip()
                print(f"🏁  [AGENT ROUTER] Final Code Asset Resolved: Clean Markdown Extraction Found.")
                return generated_sql
            elif "SELECT" in ai_response.upper():
                print(f"🏁  [AGENT ROUTER] Final Code Asset Resolved: Fallback Native Text Extraction Found.")
                return ai_response.replace("```", "").strip()
            
            print(f"🏁  [AGENT ROUTER] Loop complete. Handing text asset fallback downstream.")
            return ai_response

        raise RuntimeError("Agent Loop Error: Max execution turns exceeded without resolving a statement.")

    # =========================================================================
    # 📑 PATH B: KNOWLEDGE BASE VECTOR RETRIEVAL (RAG)
    # =========================================================================
    def retrieve_relevant_documents(self, query: str, top_k: int = 5) -> str:
        """Runs semantic vector extraction against local persistent database storage."""
        if self.collection.count() == 0:
            return "No document metadata registered in Knowledge Base storage."

        # Compute query vector mapping
        query_vector = self.embedding_model.encode(query).tolist()
        
        # Query closest distance values from database indexing
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
        """Queries local text chunks and coordinates with Qwen to serve policy metrics."""
        if not self.qwen_engine_url:
            raise RuntimeError("CRITICAL: Qwen Engine endpoint address configurations are missing.")

        # Extract context vectors matching the customer query
        document_context = self.retrieve_relevant_documents(user_question, top_k=5)
        
        rag_prompt = f"""You are an authoritative enterprise policy compliance assistant. 
Review the following verified reference documents carefully to construct a precise, helpful response. 

VERIFIED REFERENCE CONTEXT:
{document_context}

USER QUESTION: {user_question}

OPERATIONAL MANDATE:
- Rely strictly on the information provided in the reference context above. 
- If the answer cannot be found or implied from the provided context text, state clearly that you do not possess that information in your manuals. Do not speculate or hallucinate facts."""

        payload = {
            "model": os.getenv("QWEN_MODEL", "qwen2.5-3b-instruct"),
            "messages": [{"role": "user", "content": rag_prompt}],
            "temperature": 0.2
        }

        try:
            req = urllib.request.Request(
                self.qwen_engine_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.api_token}"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"RAG Processing Failure: Could not reach inference container engine: {str(e)}"