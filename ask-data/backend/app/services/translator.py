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

        # 2. Package the schema and send it to the standalone Qwen Engine Application
        payload = {
            "model": "qwen2.5-1.5b-instruct",
            "messages": [
                {"role": "system", "content": system_context},
                {"role": "user", "content": f"Translate this question into a raw MySQL SELECT query. Do not include markdown wraps or explanations: {user_question}"}
            ],
            "temperature": 0.0
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