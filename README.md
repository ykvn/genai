```
GENAI/ask-data
├── backend/                                                     # Central FastAPI Application Cluster
│   ├── app/                                                     # Modular source packages for the web application tier
│   │   ├── core/                                                # Ingestion and background orchestration components
│   │   │   └── ingest.py                                        # Chunking, embedding generation, and vector insertion script
│   │   ├── schemas/                                             # Data validation models (Pydantic models)
│   │   │   ├── .gitkeep                                         # Preserves empty folder tracking in git
│   │   │   └── query.py                                         # Structural definitions validating incoming JSON query payloads
│   │   ├── services/                                            # Core logic and agent routing microservices
│   │   │   ├── .gitkeep                                         # Preserves empty folder tracking in git
│   │   │   └── translator.py                                    # Dual-path CrewAI execution layer (Direct SQL Context vs RAG Engine)
│   │   ├── __init__.py                                          # Forces directory tracking as an importable package module
│   │   ├── database.py                                          # Establishes relational engine connection pools and transaction setups
│   │   └── main.py                                              # Main FastAPI router managing endpoints, CORS, and exception routing
│   ├── chroma_db/                                               # Persistent local vector database storage layer (Chroma/SQLite)
│   ├── backend_entry.py                                         # Dependency installation script, reverse proxy binder, and Uvicorn boot engine
│   ├── domain_config.yaml                                       # Static domain environments, model specifications, and target parameters
│   ├── requirements.txt                                         # Defines global Python packages required for the core application tier
│   └── test_connection.py                                       # Network utility testing database loopbacks prior to application launch
├── data/                                                        # Raw Documents Unstructured Data Ingestion Layer
│   └── documents/                                               # Staging subfolder for raw compliance manual files
│       ├── .gitkeep                                             # Track subfolder constraints in git repository
│       └── KEBIJAKAN KOMUNIKASI DENGAN PEMEGANG SAHAM...pdf     # Corporate standard policy template used for vector ingestion
├── data_generation/                                             # Seeding Utilities for Relational Testing Data
│   └── generate_synthetic.py                                    # Auto-populates target relational database with simulated transaction arrays
├── frontend/                                                    # User Interface Panel Environment
│   ├── app/                                                     # Client UI configuration assets, styles, and dashboard templates
│   │   └── .gitkeep                                             # Tracks frontend app workspace parameters in git
│   ├── frontend_entry.py                                        # Launches frontend process loops and registers subdomains inside CML gateway
│   └── package.json                                             # Manages frontend JavaScript modules, deployment scripts, and compiler settings
├── litellm_proxy/                                               # Open-Source API Standardizer & Fallback Middleware
│   ├── litellm_config.yaml                                      # Model routing maps binding OpenAI requests to target raw Qwen engine setups
│   └── proxy_entry.py                                           # Binds proxy settings to port 8100 and monitors incoming network data
├── mcp_server/                                                  # Model Context Protocol Unified Data Layer
│   ├── app/                                                     # Modular wrapper containing structural agent tooling scripts
│   │   └── tools/                                               # Concrete automation hooks exposed to the application LLM layers
│   │       ├── dormant_risk.py                                  # Inspects databases to detect high-risk static/dormant client accounts
│   │       ├── rag_search.py                                    # Context extraction tool offering direct semantic access to vector stores
│   │       └── sql_query.py                                     # Standard tool allowing external query processing blocks against databases
│   ├── mcp_entry.py                                             # Hosts the custom MCP endpoint logic inside an independent API microservice
│   └── requirements.txt                                         # Lists packages specifically assigned to handle context standardizations
├── qwen_inference/                                              # Localized CPU Generation & Execution Stack
│   ├── download_cpu_model.py                                    # Automates GGUF model quantization pull routines from Hugging Face models
│   ├── download_model.py                                        # Utility managing baseline weight collection frameworks
│   ├── qwen_cpu_entry.py                                        # Runs highly optimized CPU generations using llama-cpp-python packages
│   ├── qwen_entry.py                                            # Standard baseline generation microservice targeting general execution tracks
│   └── requirements.txt                                         # Provisioning toolsets handling matrix multiplications and local model layers
├── sql/                                                         # Relational Database Target DDL Definitions
│   └── schema.sql                                               # Contains formal script commands (CREATE TABLE) to formulate database assets
├── scripts/                                                     # Enterprise Setup and Container Provisioning
│   └── cml_bootstrap.sh                                         # Core shell execution setup defining OS privileges and standard system packages
├── .gitignore                                                   # Restricts large models, persistent operational logs, and weights from Git
└── README.md                                                    # Master architectural guide detailing installation steps and dependencies
```
