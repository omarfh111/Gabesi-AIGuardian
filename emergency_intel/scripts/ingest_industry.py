import os
import fitz  # PyMuPDF
import logging
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI
from langsmith import wrappers
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from uuid import uuid4

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('IndustryIngester')

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

COLLECTION_NAME = "gabes_industry"
INPUT_DIR = "data_an/raw/industry"
CHUNK_SIZE_WORDS = 400
CHUNK_OVERLAP_WORDS = 50

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text() + " "
    return text

def chunk_text(text, chunk_size, chunk_overlap):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - chunk_overlap
    return chunks

def ingest_industry_data():
    if not QDRANT_URL or not QDRANT_API_KEY or not OPENAI_API_KEY:
        logger.error("Missing Qdrant or OpenAI API keys in .env")
        return

    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    openai_client = wrappers.wrap_openai(OpenAI(api_key=OPENAI_API_KEY))

    # Check if collection exists. If not, create it. Additive process.
    try:
        client.get_collection(collection_name=COLLECTION_NAME)
        logger.info(f"Collection {COLLECTION_NAME} exists. Using additive ingestion.")
    except Exception:
        logger.info(f"Creating collection {COLLECTION_NAME}...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=3072, distance=Distance.COSINE),
        )

    if not os.path.exists(INPUT_DIR):
        logger.error(f"Directory not found: {INPUT_DIR}")
        return

    all_chunks = []
    logger.info(f"Extracting and chunking text from PDFs in {INPUT_DIR}")
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".pdf"):
            pdf_path = os.path.join(INPUT_DIR, filename)
            logger.info(f"Processing {filename}...")
            text = extract_text_from_pdf(pdf_path)
            chunks = chunk_text(text, CHUNK_SIZE_WORDS, CHUNK_OVERLAP_WORDS)
            
            for chunk in chunks:
                if len(chunk.strip()) > 50:
                    all_chunks.append({
                        "text": chunk,
                        "source": filename
                    })

    if not all_chunks:
        logger.warning("No chunks found to ingest.")
        return

    logger.info(f"Embedding and uploading {len(all_chunks)} chunks to Qdrant using text-embedding-3-large...")
    
    # Process in batches
    batch_size = 50
    for i in tqdm(range(0, len(all_chunks), batch_size)):
        batch = all_chunks[i:i + batch_size]
        texts = [item["text"] for item in batch]
        metadatas = [{"source": item["source"], "text": item["text"]} for item in batch]
        
        response = openai_client.embeddings.create(input=texts, model="text-embedding-3-large")
        vectors = [item.embedding for item in response.data]
        
        points = [
            PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload=metadata
            )
            for vector, metadata in zip(vectors, metadatas)
        ]
        
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
    logger.info("Ingestion completed successfully.")

if __name__ == "__main__":
    ingest_industry_data()
