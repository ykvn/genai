import os

# 🩹 ENTERPRISE LINUX RUNTIME PATCH: Swaps out outdated system SQLite layouts 
# with the binary layout required by ChromaDB before importing the database module.
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import chromadb
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

def run_auto_ingest(docs_dir: str, persist_dir: str, collection_name: str):
    """
    Scans the local documents directory for new policy manuals, extracts raw text strings,
    computes local mathematical vector embeddings, and stores them securely inside ChromaDB.
    """
    # 1. Establish database baseline mapping
    chroma_client = chromadb.PersistentClient(path=persist_dir)
    collection = chroma_client.get_or_create_collection(name=collection_name)
    
    # Check if the store already contains active nodes to prevent redundant vectorizing loops
    if collection.count() > 0:
        print(f"✅ [RAG ENGINE] ChromaDB collection '{collection_name}' already contains {collection.count()} active structural fragments. Skipping ingest cycle.")
        return

    # 2. Inspect filesystem for asset targets
    if not os.path.exists(docs_dir):
        print(f"⚠️ [RAG ENGINE] Targeted directory path does not exist: '{docs_dir}'. Sync cycle suspended.")
        return

    pdf_files = [f for f in os.listdir(docs_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"⚠️ [RAG ENGINE] No source policy manuals detected inside '{docs_dir}'. Knowledge base remains empty.")
        return

    # 3. Spin up the localized Transformer brain (Runs completely within your 4 vCPU layer)
    print("🧠 [RAG ENGINE] Loading local all-MiniLM-L6-v2 vectorization engine weights...")
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    global_chunk_counter = 0

    # 4. Core Processing Assembly Line
    for pdf_file in pdf_files:
        file_path = os.path.join(docs_dir, pdf_file)
        print(f"📄 [RAG ENGINE] Parsing asset parameters from: {pdf_file}")
        
        try:
            reader = PdfReader(file_path)
            raw_document_text = ""
            
            # Extract and merge characters page-by-page safely
            for page_idx, page in enumerate(reader.pages):
                extracted_text = page.extract_text()
                if extracted_text:
                    raw_document_text += extracted_text + "\n"

            # Structural text segmentation block (~500 characters with a 100 character slide overlap)
            chunk_size = 500
            overlap = 100
            text_fragments = []
            
            for i in range(0, len(raw_document_text), chunk_size - overlap):
                fragment = raw_document_text[i:i + chunk_size].strip()
                # Skip meaningless micro-strings or parsing artifacts
                if len(fragment) > 50:
                    text_fragments.append(fragment)

            if not text_fragments:
                print(f"⚠️ [RAG ENGINE] Warning: Unreadable or image-only formatting layout detected in {pdf_file}. Skipping.")
                continue

            print(f"✂️ [RAG ENGINE] Fragmented document into {len(text_fragments)} text segments. Computing vector tokens...")
            
            # 5. Math Mapping Layer (Translates sentences into structural vectors)
            vector_embeddings = embedding_model.encode(text_fragments).tolist()
            
            # 6. Database Registration Layer
            document_ids = [f"chunk_{global_chunk_counter + idx}" for idx in range(len(text_fragments))]
            metadata_payloads = [{"source_file": pdf_file} for _ in text_fragments]
            
            collection.add(
                documents=text_fragments,
                embeddings=vector_embeddings,
                metadatas=metadata_payloads,
                ids=document_ids
            )
            
            global_chunk_counter += len(text_fragments)
            print(f"💾 [RAG ENGINE] Successfully committed {len(text_fragments)} vector items for {pdf_file} to disk storage.")
            
        except Exception as file_error:
            print(f"❌ [RAG ENGINE] Critical crash while parsing content fields for {pdf_file}: {str(file_error)}")
            continue

    print(f"🎉 [RAG ENGINE] Database build pipeline resolved! {collection.count()} total vectors are active in the cluster.")