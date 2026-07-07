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

        # Concise instruction set optimized for a 1.5B model
        instructional_system_prompt = f"""You are a strict read-only Text-to-SQL engine for a MySQL 8.0 database.
You must transform user requests into executable SQL code blocks.

Here is your schema metadata:
{system_context}

CRITICAL: The 'customers' table does NOT have a 'status' column. To find active customers, you MUST join with the 'savings' table."""

        # 🧠 FEW-SHOT INSTRUCTION LAYER: Train the 1.5B model with explicit pairs
        payload = {
            "model": "qwen2.5-1.5b-instruct",
            "messages": [
                {"role": "system", "content": instructional_system_prompt},
                
                # Example 1: Resolving the "active customers" schema limitation
                {"role": "user", "content": "Translate this question into a single valid MySQL statement: show active customers"},
                {"role": "assistant", "content": "SELECT c.* FROM customers c INNER JOIN savings s ON c.customer_id = s.customer_id WHERE s.status = 'ACTIVE';"},
                
                # Example 2: Resolving specific bank filters
                {"role": "user", "content": "Translate this question into a single valid MySQL statement: Show me active customers where bank_name is BNI"},
                {"role": "assistant", "content": "SELECT c.* FROM customers c INNER JOIN savings s ON c.customer_id = s.customer_id WHERE c.bank_name = 'BNI' AND s.status = 'ACTIVE';"},
                
                # Example 3: Blocking data modification actions safely
                {"role": "user", "content": "Translate this question into a single valid MySQL statement: Update customers from bank BNI"},
                {"role": "assistant", "content": "SELECT * FROM customers WHERE bank_name = 'BNI';"},
                
                # The real, live incoming question
                {"role": "user", "content": f"Translate this question into a single valid MySQL statement: {user_question}"}
            ],
            "temperature": 0.0  # Keep it perfectly deterministic
        }

        try:
            req = urllib.request.Request(
                self.qwen_engine_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            # 🔄 CHANGE TIMEOUT FROM 10 TO 60 SECONDS
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                generated_sql = result["choices"][0]["message"]["content"].strip()
                
                # Clean up any accidental markdown wrappers
                if generated_sql.startswith("```"):
                    generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()
                
                return generated_sql
        except Exception as e:
            raise RuntimeError(f"Qwen Engine Server Application at port 8001 is unreachable: {str(e)}")