# ask-data/backend/app/services/translator.py
import os
import yaml

class SQLTranslationService:
    def __init__(self):
        # Dynamically locate domain_config.yaml relative to this service file
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_path = os.path.join(base_dir, "domain_config.yaml")
        self.domain_data = self._load_config()

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
        
        # 🏗️ Begin assembling the strict system core prompt instructions
        prompt = f"You are a world-class text-to-SQL translation engine specializing in native {db_type} syntax.\n"
        prompt += f"You translate natural language questions regarding '{domain_name}' into secure SQL queries.\n\n"
        prompt += "--- DATABASE SCHEMA SCHEMA DICTIONARY ---\n"
        
        # Parse out tables, explicit column configurations, types, and primary/foreign key connections
        for table_name, details in tables.items():
            prompt += f"Table: {table_name}\n"
            prompt += f"Description: {details.get('description', '')}\n"
            prompt += "Columns:\n"
            
            for col_name, meta in details.get("columns", {}).items():
                col_type = meta.get("type", "VARCHAR")
                desc = meta.get("description", "")
                
                # Check for table constraint flags
                pk = " [PRIMARY KEY]" if meta.get("primary_key") else ""
                ref = f" [JOINS/REFERENCES -> {meta.get('references')}]" if meta.get("references") else ""
                
                prompt += f"  - {col_name} ({col_type}){pk}{ref}: {desc}\n"
            prompt += "\n"
            
        # Append target date calculations and operational rules
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