import os
import json
import urllib.request

class SQLTranslationService:
    def __init__(self):
        # Dynamically point to your other standalone Cloudera AI Applications
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:8090")
        self.qwen_engine_url = os.getenv("QWEN_LLM_URL", "http://localhost:8001/v1/chat/completions")

    def generate_sql(self, user_question: str) -> str:
        """
        Acts as the MCP Host Client. It fetches the schema context from your Tool App,
        hands it to your Qwen App to get the SQL statement, and returns it to main.py.
        """
        # 1. Pull the live database schema from the MCP Tool Server Application
        try:
            schema_req = urllib.request.Request(f"{self.mcp_server_url}/api/test/schema")
            with urllib.request.urlopen(schema_req, timeout=5) as response:
                schema_data = json.loads(response.read().decode("utf-8"))
                system_context = schema_data.get("raw_yaml_configuration", "")
        except Exception as e:
            raise RuntimeError(f"MCP Tool Server Application at port 8090 is unreachable: {str(e)}")

        # 🧠 1.5B MODEL SCAFFOLDING: Frame the raw YAML with strict behavioral boundaries
        instructional_system_prompt = f"""You are a strict read-only Text-to-SQL translation assistant for a MySQL 8.0 database.
You must transform natural language questions into perfectly executable SQL statements.

Here is the authoritative database schema layout you MUST follow:
{system_context}

CRITICAL EXECUTION RULES:
1. You are strictly forbidden from generating INSERT, UPDATE, DELETE, or DROP commands.
2. If a user asks to modify or update data, do NOT write an UPDATE query. Instead, return a SELECT query targeting the relevant rows.
3. Use ONLY columns and tables explicitly listed in the schema definitions above.
4. Pay attention to specific column names: use 'bank_name', NEVER use 'bank'.
5. Output ONLY the raw SQL query. Do not include markdown blocks, text descriptions, or conversational prose."""

        # 2. Package the structured prompt and send it to the standalone Qwen Engine Application
        payload = {
            "model": "qwen2.5-1.5b-instruct",
            "messages": [
                {"role": "system", "content": instructional_system_prompt},
                {"role": "user", "content": f"Translate this question into a single valid MySQL statement: {user_question}"}
            ],
            "temperature": 0.0  # Kept at 0.0 to guarantee deterministic, non-hallucinated queries
        }

        try:
            req = urllib.request.Request(
                self.qwen_engine_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode("utf-8"))
                generated_sql = result["choices"][0]["message"]["content"].strip()
                
                # Clean up any accidental markdown wrappers
                if generated_sql.startswith("```"):
                    generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
                
                return generated_sql
        except Exception as e:
            raise RuntimeError(f"Qwen Engine Server Application at port 8001 is unreachable: {str(e)}")