import os
import re
import sys
import json
import time
import uuid
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone
import warnings

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from openai import OpenAI
from pypdf import PdfReader
from tqdm import tqdm

from chonkie import SemanticChunker

# Load environment
load_dotenv()
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Constants
VECTOR_SIZE = 3072
EMBEDDING_MODEL = "text-embedding-3-large"
NAMESPACE_URL = uuid.NAMESPACE_URL
BATCH_SIZE = 50
QDRANT_UPSERT_BATCH_SIZE = 100

# Path setup
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Optional: suppress extraneous warnings from pypdf
warnings.filterwarnings("ignore", category=UserWarning, module="pypdf")

def setup_logging():
    log_dir = BASE_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logging.basicConfig(
        filename=log_dir / f"ingestion_{timestamp}.log",
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    logging.getLogger('').addHandler(console)

def ensure_collections_exist(client: QdrantClient) -> int:
    collections = [c.name for c in client.get_collections().collections]
    collections_created = 0
    
    # 1. gabes_knowledge
    if "gabes_knowledge" not in collections:
        client.create_collection(
            collection_name="gabes_knowledge",
            vectors_config=qmodels.VectorParams(size=VECTOR_SIZE, distance=qmodels.Distance.COSINE),
            sparse_vectors_config={"text-sparse": qmodels.SparseVectorParams(modifier=qmodels.Modifier.IDF)}
        )
        client.create_payload_index("gabes_knowledge", "source_type", field_schema=qmodels.PayloadSchemaType.KEYWORD)
        client.create_payload_index("gabes_knowledge", "language", field_schema=qmodels.PayloadSchemaType.KEYWORD)
        client.create_payload_index("gabes_knowledge", "doc_name", field_schema=qmodels.PayloadSchemaType.KEYWORD)
        logging.info("Created collection: gabes_knowledge")
        collections_created += 1
    
    # 2. satellite_timeseries
    if "satellite_timeseries" not in collections:
        client.create_collection(
            collection_name="satellite_timeseries",
            vectors_config=qmodels.VectorParams(size=VECTOR_SIZE, distance=qmodels.Distance.COSINE)
        )
        client.create_payload_index("satellite_timeseries", "plot_id", field_schema=qmodels.PayloadSchemaType.KEYWORD)
        client.create_payload_index("satellite_timeseries", "week", field_schema=qmodels.PayloadSchemaType.KEYWORD)
        logging.info("Created collection: satellite_timeseries")
        collections_created += 1
    
    # 3. farmer_context
    if "farmer_context" not in collections:
        client.create_collection(
            collection_name="farmer_context",
            vectors_config=qmodels.VectorParams(size=VECTOR_SIZE, distance=qmodels.Distance.COSINE)
        )
        client.create_payload_index("farmer_context", "farmer_id", field_schema=qmodels.PayloadSchemaType.KEYWORD)
        logging.info("Created collection: farmer_context")
        collections_created += 1
        
    return collections_created

def get_embeddings(texts: list[str], client: OpenAI, retries=3) -> tuple[list[list[float]], int]:
    for attempt in range(retries):
        try:
            response = client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
            return [data.embedding for data in response.data], response.usage.total_tokens
        except Exception as e:
            wait_time = 2 ** attempt
            logging.warning(f"Error fetching embeddings: {e}. Retrying in {wait_time}s...")
            if attempt == retries - 1:
                logging.error("Failed to fetch embeddings after max retries.")
                raise e
            time.sleep(wait_time)

def batched_upsert(client: QdrantClient, collection_name: str, points: list[qmodels.PointStruct], retries=3):
    for i in range(0, len(points), QDRANT_UPSERT_BATCH_SIZE):
        batch = points[i:i + QDRANT_UPSERT_BATCH_SIZE]
        for attempt in range(retries):
            try:
                client.upsert(collection_name=collection_name, points=batch)
                break
            except Exception as e:
                wait_time = 2 ** attempt
                if attempt == retries - 1:
                    logging.error(f"Failed to upsert batch after {retries} retries: {e}")
                    raise
                logging.warning(f"Upsert failed: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)

def is_doc_in_qdrant(client: QdrantClient, collection_name: str, doc_name: str) -> bool:
    try:
        result = client.count(
            collection_name=collection_name,
            count_filter=qmodels.Filter(
                must=[
                    qmodels.FieldCondition(
                        key="doc_name",
                        match=qmodels.MatchValue(value=doc_name)
                    )
                ]
            ),
            exact=True,
        )
        return result.count > 0
    except Exception as e:
        logging.warning(f"Could not checking resume status for {doc_name}: {e}")
        return False

def configure_documents() -> list[dict]:
    docs = []
    
    # Group A
    pdl_md = DATA_DIR / "processed" / "PDL_GABES_clean.md"
    if pdl_md.exists():
        docs.append({"path": pdl_md, "lang": "fr", "type": "pdl_report", "is_md": True, "is_json": False})
        
    # Group B & D
    pdl_dir = DATA_DIR / "pdl_reports"
    arabic_pdf_name = "ملخص الدراسة الاستراتيجية للجنوب 2015-2035.pdf"
    if pdl_dir.exists():
        for file in pdl_dir.glob("*.pdf"):
            if file.name == arabic_pdf_name:
                docs.append({"path": file, "lang": "ar", "type": "strategic_study", "is_md": False, "is_json": False})
            else:
                docs.append({"path": file, "lang": "fr", "type": "pdl_report", "is_md": False, "is_json": False})
                
    # Group C
    papers_dir = DATA_DIR / "papers"
    if papers_dir.exists():
        for file in papers_dir.glob("*.pdf"):
            docs.append({"path": file, "lang": "en", "type": "scientific_paper", "is_md": False, "is_json": False})
            
    # Group E
    fao_ref = DATA_DIR / "references" / "Allen_FAO1998.pdf"
    if fao_ref.exists():
        docs.append({"path": fao_ref, "lang": "en", "type": "reference", "is_md": False, "is_json": False})
        
    # Group F
    json_dir = DATA_DIR / "structured"
    if json_dir.exists():
        for file in json_dir.glob("*.json"):
            docs.append({"path": file, "lang": "en", "type": "structured_data", "is_md": False, "is_json": True})
            
    return docs

def extract_pdf_lines(filepath: Path) -> str:
    reader = PdfReader(filepath)
    text_pages = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_pages.append(page_text)
    return "\n\n".join(text_pages)

def chunk_markdown(text: str, chunker: SemanticChunker) -> list[str]:
    lines = text.split("\n")
    chunks = []
    
    def is_table_line(l: str) -> bool:
        return l.strip().startswith("|")
    
    current_lines = []
    parsing_table = False
    
    for line in lines:
        if is_table_line(line):
            if not parsing_table:
                if current_lines:
                    prose_text = "\n".join(current_lines).strip()
                    if prose_text:
                        prose_chunks = [c.text for c in chunker.chunk(prose_text)]
                        chunks.extend(prose_chunks)
                    current_lines = []
                parsing_table = True
            current_lines.append(line)
        else:
            if parsing_table:
                if current_lines:
                    table_text = "\n".join(current_lines).strip()
                    if table_text:
                        chunks.append(table_text) # single chunk
                    current_lines = []
                parsing_table = False
            current_lines.append(line)
            
    if current_lines:
        text_joined = "\n".join(current_lines).strip()
        if text_joined:
            if parsing_table:
                chunks.append(text_joined)
            else:
                prose_chunks = [c.text for c in chunker.chunk(text_joined)]
                chunks.extend(prose_chunks)
            
    return chunks

def extract_and_chunk(doc: dict, chunker: SemanticChunker) -> tuple[list[str], dict]:
    filepath = doc["path"]
    filename = filepath.name
    extra_payload = {}
    
    if doc["is_json"]:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        text_repr = json.dumps(data, ensure_ascii=False)
        extra_payload = {"structured_payload": data}
        if len(json.dumps(extra_payload)) > 60000:
            logging.warning(f"Payload for {filename} is > 60000 chars, storing only top-level keys.")
            extra_payload = {"structured_payload": list(data.keys())} if isinstance(data, dict) else {"structured_payload": "too large"}
        return [text_repr], extra_payload
        
    elif doc["is_md"]:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()
        return chunk_markdown(text, chunker), extra_payload
        
    else: # PDF
        text = extract_pdf_lines(filepath)
        if len(text.strip()) < 100:
            logging.warning(f"[WARN] {filename}: only {len(text)} chars extracted — may be scanned PDF, skipping")
            return [], extra_payload
        return [c.text for c in chunker.chunk(text)], extra_payload

def main():
    parser = argparse.ArgumentParser(description="Ingest docs for Gabès Farmer AI Qdrant Collections.")
    parser.add_argument("--resume", action="store_true", help="Skip documents completely present in Qdrant")
    parser.add_argument("--dry-run", action="store_true", help="Run full pipeline without upserting to Qdrant")
    parser.add_argument("--doc", type=str, help="Ingest only a specific document by filename")
    args = parser.parse_args()

    setup_logging()
    
    # Init Clients
    openai_client = OpenAI(api_key=OPENAI_API_KEY)
    
    collections_created = 0
    if not args.dry_run:
        qdrant_client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60, prefer_grpc=False)
        collections_created = ensure_collections_exist(qdrant_client)
    else:
        qdrant_client = None

    logging.info("Loading embedding model for SemanticChunker...")
    print("Note: downloading embedding model (~420MB) on first run.")
    print("Loading Chonkie semantic chunker model (this may take a minute on first run)...")
    
    # Initialize Chonkie Chunker
    chunker = SemanticChunker(
        embedding_model="sentence-transformers/paraphrases-multilingual-mpnet-base-v2",
        chunk_size=512,
        threshold=0.5
    )

    documents = configure_documents()
    
    if args.doc:
        documents = [d for d in documents if d["path"].name == args.doc]
        if not documents:
            print(f"Document {args.doc} not found!")
            return

    total_skipped = 0
    total_chunks_processed = 0
    total_tokens_used = 0
    total_points_upserted = 0
    start_time = time.time()

    print(f"Starting ingestion process over {len(documents)} document(s)...")

    # Document Level Loop
    for doc in tqdm(documents, desc="Processing Documents", position=0):
        filename = doc["path"].name
        
        if args.resume and not args.dry_run:
            if is_doc_in_qdrant(qdrant_client, "gabes_knowledge", filename):
                logging.info(f"Skipping {filename} because it exists (resume flag).")
                total_skipped += 1
                continue
                
        logging.info(f"Extracting and chunking {filename}...")
        try:
            chunks, extra_payload = extract_and_chunk(doc, chunker)
        except Exception as e:
            logging.error(f"Failed to chunk {filename}: {e}")
            continue
            
        if not chunks:
            continue
            
        total_chunks_processed += len(chunks)
        points_to_upsert = []
        
        # Batch Embeddings Loop
        for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc=f"Embedding {filename}", position=1, leave=False):
            batch_texts = chunks[i:i + BATCH_SIZE]
            
            if args.dry_run:
                total_tokens_used += sum(len(t) // 4 for t in batch_texts)
                continue
                
            try:
                embeddings, tokens = get_embeddings(batch_texts, openai_client)
            except Exception as e:
                logging.error(f"Failed to embed chunks {i} to {i+len(batch_texts)} in {filename}: {e}")
                continue
                
            total_tokens_used += tokens
            
            for j, (text, emb) in enumerate(zip(batch_texts, embeddings)):
                chunk_index = i + j
                point_id = str(uuid.uuid5(NAMESPACE_URL, f"{filename}::{chunk_index}"))
                
                payload = {
                    "text": text,
                    "doc_name": filename,
                    "source_type": doc["type"],
                    "language": doc["lang"],
                    "chunk_index": chunk_index,
                    "total_chunks": len(chunks),
                    "char_count": len(text),
                    "ingested_at": datetime.now(timezone.utc).isoformat()
                }
                
                if doc["is_json"]: 
                    payload.update(extra_payload)
                    
                points_to_upsert.append(qmodels.PointStruct(id=point_id, vector=emb, payload=payload))
            
            time.sleep(0.5) # rate limit sleep
            
        if not args.dry_run and points_to_upsert:
            logging.info(f"Upserting {len(points_to_upsert)} points for {filename} to Qdrant...")
            try:
                batched_upsert(qdrant_client, "gabes_knowledge", points_to_upsert)
                total_points_upserted += len(points_to_upsert)
            except Exception as e:
                logging.error(f"Failed to complete upsert for {filename}: {e}")

    elapsed = time.time() - start_time
    
    # Print summary
    print("\n" + "+" + "-" * 46 + "+")
    print("|  INGESTION SUMMARY                           |")
    print("+" + "-" * 46 + "+")
    print(f"|  Documents processed : {len(documents):<21} |")
    print(f"|  Documents skipped   : {total_skipped:<21} |")
    print(f"|  Total chunks        : {total_chunks_processed:<21} |")
    print(f"|  Total points upserted: {total_points_upserted:<20} |")
    print(f"|  Estimated tokens used: ~{total_tokens_used:<19} |")
    print(f"|  Collections created : {collections_created:<21} |")
    print(f"|  Time elapsed        : {int(elapsed):<20}s |")
    print("+" + "-" * 46 + "+\n")

if __name__ == "__main__":
    main()
