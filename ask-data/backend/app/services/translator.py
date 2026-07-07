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
        Pure MCP Agent Router. It exposes a tool matrix to Qwen and manages
        a dynamic execution loop based on the model's operational requests.
        """
        
        # 🧠 1. Define the authoritative tool menu and formatting contract for the 3B model
        agent_system_prompt = """You are an autonomous database routing agent for a MySQL 8.0 cluster. 
You do not have the data schema memorized. You must interact with your available Model Context Protocol (MCP) tools to discover information before outputting code.

AVAILABLE MCP TOOLS:
1. Name: `get_schema()`
   Description: Connects to the local filesystem and reads the master 'domain_config.yaml' file containing table metrics, columns, aliases, and active state rules.

OPERATIONAL INSTRUCTIONS:
- If you do not know the exact column names, table links, or active state rules needed for a query, you MUST request the schema by writing exactly:
  CALL: get_schema()
- Once you receive the tool response with the schema text layout, process the table properties carefully.
- Output your final response as a single, raw MySQL statement wrapped inside a clean ```sql ``` code block. Do not write text explanations outside the code block once you have your answer.

CRITICAL SAFETY BOUNDARIES:
- You are strictly forbidden from writing INSERT, UPDATE, DELETE, or DROP commands.
- Only reference column names explicitly defined in the tool output (e.g., use 'bank_name', NEVER use 'bank').
- To show active customers, you MUST INNER JOIN 'customers' with 'savings' and filter WHERE savings.status = 'ACTIVE'."""

        # 🔄 Initialize conversation history thread
        messages = [
            {"role": "system", "content": agent_system_prompt},
            {"role": "user", "content": f"Analyze this request and generate the correct query: {user_question}"}
        ]

        # Allow the agent up to 3 evaluation turns to trigger tools dynamically
        for turn in range(3):
            payload = {
                "model": "qwen2.5-3b-instruct",
                "messages": messages,
                "temperature": 0.0 # Forced determinism to eliminate hallucinations
            }

            # Ship conversational frame to your Qwen engine container
            try:
                req = urllib.request.Request(
                    self.qwen_engine_url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=30) as response:
                    result = json.loads(response.read().decode("utf-8"))
                    ai_response = result["choices"][0]["message"]["content"].strip()
            except Exception as e:
                raise RuntimeError(f"Qwen Engine Server at port 8001 is unreachable: {str(e)}")

            # 🔍 Log the agent's internal thought stream directly to your backend stdout terminal
            print(f"🤖 [Pure MCP Agent - Turn {turn + 1}] Qwen Output:\n{ai_response}\n")

            # INTERCEPT ACTION 1: Check if the model is calling the schema tool
            if "CALL: get_schema()" in ai_response:
                print("📡 Tool Invoked! Fetching structural layout from MCP Server Application...")
                try:
                    schema_req = urllib.request.Request(f"{self.mcp_server_url}/api/test/schema")
                    with urllib.request.urlopen(schema_req, timeout=5) as schema_resp:
                        schema_data = json.loads(schema_resp.read().decode("utf-8"))
                        schema_context = schema_data.get("raw_yaml_configuration", "")
                except Exception as e:
                    raise RuntimeError(f"MCP Tool Server failed during dynamic tool call: {str(e)}")

                # Update the conversational chain with the tool trigger and the real data response
                messages.append({"role": "assistant", "content": ai_response})
                messages.append({
                    "role": "user", 
                    "content": f"TOOL_RESPONSE (get_schema):\n{schema_context}\n\nReview this data and generate your final raw MySQL statement inside ```sql wrappers."
                })
                # Re-loop: The model will read this data on the very next turn!
                continue

            # INTERCEPT ACTION 2: The model has processed the context and generated the final SQL asset
            if "```sql" in ai_response:
                generated_sql = ai_response.split("```sql")[1].split("```")[0].strip()
                return generated_sql
            elif "SELECT" in ai_response.upper():
                # Safe fallback configuration if the model omits markdown wraps but writes clean code
                return ai_response.replace("```", "").strip()
            
            # Catch-all if the model returns an error narrative or blocks a write query
            return ai_response

        raise RuntimeError("Agent Loop Error: Max execution turns exceeded without resolving a statement.")