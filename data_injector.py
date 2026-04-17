import os
import glob
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings

# Load environment variables
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([QDRANT_URL, QDRANT_API_KEY, OPENAI_API_KEY]):
    print("Error: Missing environment variables (QDRANT_URL, QDRANT_API_KEY, or OPENAI_API_KEY)")
    exit(1)

COLLECTION_NAME = "gabesi_medical_assistant"
DATA_DIR = r"c:\Users\Omar\Desktop\Gabsi\Gabesi-AIGuardian\data\dataassistantmed"

def inject_data():
    # 1. Initialize Qdrant Client
    print(f"Connecting to Qdrant at {QDRANT_URL}...")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # 2. Check/Create Collection
    collections = client.get_collections().collections
    exists = any(c.name == COLLECTION_NAME for c in collections)

    if not exists:
        print(f"Creating collection '{COLLECTION_NAME}'...")
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
        )
    else:
        print(f"Collection '{COLLECTION_NAME}' already exists.")

    # 3. Load PDFs
    pdf_files = glob.glob(os.path.join(DATA_DIR, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {DATA_DIR}")
        return

    print(f"Found {len(pdf_files)} PDF files. Processing...")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)

    all_chunks = []
    for pdf_path in pdf_files:
        print(f"  Loading {os.path.basename(pdf_path)}...")
        try:
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            chunks = text_splitter.split_documents(docs)
            for chunk in chunks:
                chunk.metadata["source"] = os.path.basename(pdf_path)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"  Error loading {pdf_path}: {e}")

    print(f"Total chunks to inject: {len(all_chunks)}")

    # 4. Generate Embeddings and Upsert
    # We'll batch them to avoid hitting limits or memory issues
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        texts = [doc.page_content for doc in batch]
        metadatas = [doc.metadata for doc in batch]
        
        print(f"  Embedding and upserting batch {i//batch_size + 1}/{(len(all_chunks)-1)//batch_size + 1}...")
        
        # Get embeddings
        vector_list = embeddings.embed_documents(texts)
        
        # Prepare points
        points = []
        for j, vector in enumerate(vector_list):
            point_id = hash(texts[j] + str(metadatas[j])) % (2**63 - 1)  # Simple hash for ID
            # Better way is to use i + j
            point_id = i + j
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "text": texts[j],
                    "metadata": metadatas[j]
                }
            ))
        
        client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )

    print(f"\nSuccessfully injected {len(all_chunks)} chunks into '{COLLECTION_NAME}'.")
    return COLLECTION_NAME

if __name__ == "__main__":
    name = inject_data()
    if name:
        print(f"\nFinal Collection Name: {name}")
