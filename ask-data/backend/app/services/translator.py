# ask-data/backend/app/services/translator.py
import os
import json
import yaml
import urllib.request
import urllib.error

class SQLTranslationService:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(base_dir, "domain_config.yaml")
        self.domain_data = self._load_config()
        
        # Target endpoint for your upcoming local vLLM Qwen server
        self.llm_url = os.getenv("QWEN_LLM_URL", "http://localhost:8001/v1/chat/completions")

    def _load_config(self):
        """Safely parses the YAML file into a native Python dictionary"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Missing mandatory domain schema mapping at: {self.config_path}")
        with open(self.config_path, "r") as f:
            return yaml.safe_load(f)

    def build_llm_system_context(self) -> str:
        """Transforms domain_config.yaml metadata into structural prompt context for the AI"""
        if not self.domain_data:
            return ""
            
        db_type = self.domain_data.get("database_type", "MySQL 8.0")
        domain_name = self.domain_data.get("domain", "Enterprise Database")
        tables = self.domain_data.get("tables", {})
        rules = self.domain_data.get("common_rules", {})
        
        prompt = f"You are a world-class text-to-SQL translation engine specializing in native {db_type} syntax.\n"
        prompt += f"You translate natural language questions regarding '{domain_name}' into secure SQL queries.\n\n"
        prompt += "--- DATABASE SCHEMA SCHEMA DICTIONARY ---\n"
        
        for table_name, details in tables.items():
            prompt += f"Table: {table_name}\n"
            prompt += f"Description: {details.get('description', '')}\n"
            prompt += "Columns:\n"
            for col_name, meta in details.get("columns", {}).items():
                col_type = meta.get("type", "VARCHAR")
                desc = meta.get("description", "")
                pk = " [PRIMARY KEY]" if meta.get("primary_key") else ""
                ref = f" [JOINS/REFERENCES -> {meta.get('references')}]" if meta.get("references") else ""
                prompt += f"  - {col_name} ({col_type}){pk}{ref}: {desc}\n"
            prompt += "\n"
            
        prompt += "--- MANDATORY STRATEGIC TRANSLATION RULES ---\n"
        prompt += f"1. Active Accounts filtering: {rules.get('active_records', '')}\n"
        prompt += "2. Temporal/Date Math Context Macros:\n"
        for macro, sql_snippet in rules.get("temporal_queries", {}).items():
            prompt += f"   * For '{macro.replace('_', ' ')}', inject native syntax pattern: {sql_snippet}\n"
            
        prompt += "\n--- SECURITY & EXPORT RESTRICTIONS ---\n"
        prompt += f"- Read Only Constraints: {rules.get('security_guardrails', {}).get('read_only', '')}\n"
        prompt += f"- Memory Safety Bounds: {rules.get('security_guardrails', {}).get('max_limit', '')}\n\n"
        prompt += "Respond ONLY with the final clean executable SQL string wrapped in markdown tags. Do not explain the code."
        
        return prompt

    def generate_sql(self, user_question: str) -> str:
        """Beams the prompt payload to vLLM, with an automated fallback for testing"""
        system_prompt = self.build_llm_system_context()
        
        # Prepare standard OpenAI-compatible JSON payload for vLLM
        payload = {
            "model": "qwen2.5-14b-instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Translate this question into executable SQL: {user_question}"}
            ],
            "temperature": 0.0  # Zero out creativity for deterministic SQL generation
        }
        
        try:
            # Attempt a live HTTP POST call to your upcoming vLLM server
            req = urllib.request.Request(
                self.llm_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                result = json.loads(response.read().decode("utf-8"))
                # Extract response text from standard chat completion schema
                raw_sql = result["choices"][0]["message"]["content"]
                return self._clean_markdown_sql(raw_sql)
                
        except (urllib.error.URLError, Exception):
            # 🔄 Testing Fallback: Runs automatically if vLLM server is not up yet
            print("⚠️ vLLM server offline or unreachable. Using deterministic simulation fallback...")
            return self._simulate_llm_sql(user_question)

    def _clean_markdown_sql(self, raw_output: str) -> str:
        """Strips away markdown wrappers (```sql ... ```) if returned by the LLM"""
        clean_text = raw_output.replace("```sql", "").replace("```", "").strip()
        if not clean_text.endswith(";"):
            clean_text += ";"
        return clean_text

    def _simulate_llm_sql(self, question: str) -> str:
        """Intelligent pattern matcher ensuring we can test the entire pipeline instantly"""
        q = question.lower()
        if "loan" in q:
            return "SELECT * FROM loans WHERE status = 'ACTIVE' LIMIT 100;"
        elif "saving" in q or "wealth" in q:
            return "SELECT * FROM savings WHERE status = 'ACTIVE' ORDER BY balance DESC LIMIT 100;"
        elif "birthday" in q:
            return "SELECT first_name, last_name, birth_date FROM customers WHERE WEEK(birth_date) = WEEK(CURDATE()) LIMIT 100;"
        else:
            return "SELECT * FROM customers LIMIT 100;"