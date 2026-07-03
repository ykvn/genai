bank-abc/
├── ask-data/                        # Bank ABC — Customer Analytics PoC
│   ├── backend/                     # FastAPI + NL-to-SQL + ChromaDB RAG
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── database.py          # MySQL SQLAlchemy connection layer
│   │   │   ├── main.py              # FastAPI application core
│   │   │   ├── services/            # LLM prompt construction & SQL execution
│   │   │   └── schemas/             # Pydantic data validation models
│   │   ├── domain_config.yaml       # Metadata mapping table/column descriptions
│   │   └── backend_entry.py         # CML Application Entry Point (FastAPI)
│   ├── frontend/                    # Next.js 15 UI with Cloudera Design Language
│   │   ├── app/
│   │   ├── package.json
│   │   └── frontend_entry.py        # CML Application Entry Point (Node/Next.js)
│   ├── mcp_server/                  # Model Context Protocol Server
│   │   ├── app/
│   │   │   └── tools/
│   │   │       ├── sql_query.py     # Executes generated SQL safely
│   │   │       ├── dormant_risk.py  # Analytical calculation tool
│   │   │       └── rag_search.py    # Vector search tool for unstructured data
│   │   └── mcp_entry.py             # CML Application Entry Point (MCP daemon)
│   ├── qwen_inference/              # local vLLM Server (Qwen2.5-14B-Instruct-AWQ)
│   │   ├── qwen_entry.py            # CML Models/Applications Entry Point (GPU)
│   │   └── download_model.py        # Hugging Face downloader script
│   ├── data/
│   │   └── documents/               # Internal documentation PDFs for context RAG
│   ├── chroma_db/                   # Local Vector Store (Auto-generated)
│   ├── sql/
│   │   └── schema.sql               # MySQL DDL & Seed Script
│   └── data_generation/
│       └── generate_synthetic.py    # Python Script for scaling to 10k rows
├── scripts/
│   └── cml_bootstrap.sh             # Automation script to install dependencies
└── README.md
