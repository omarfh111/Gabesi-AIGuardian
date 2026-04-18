import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant

# Load environment variables from .env file
load_dotenv()

# Define paths and names
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_path = os.path.join(base_dir, "data", "dataassistantmed")
collection_name = "medical_assistant_docs"

qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

def main():
    print(f"Loading PDFs from {data_path}...")
    loader = PyPDFDirectoryLoader(data_path)
    docs = loader.load()
    print(f"Loaded {len(docs)} pages.")

    print("Splitting documents...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")

    from qdrant_client import QdrantClient
    from qdrant_client.models import Distance, VectorParams

    print("Generating embeddings and pushing to Qdrant...")
    embeddings = OpenAIEmbeddings()

    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    
    # recreate collection to mimic force_recreate=True
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name)
    
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
    )

    qdrant = Qdrant(
        client=client, 
        collection_name=collection_name, 
        embeddings=embeddings
    )
    
    qdrant.add_documents(chunks)

    print(f"Successfully injected documents into collection: '{collection_name}'")

if __name__ == "__main__":
    main()
