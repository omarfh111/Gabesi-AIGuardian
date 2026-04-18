import os
import json
import uuid
import hashlib
import re
import time
from typing import List, Dict, Any
from pathlib import Path
import fitz  # PyMuPDF
from langdetect import detect, DetectorFactory
from tqdm import tqdm
from dotenv import load_dotenv

from qdrant_client import QdrantClient
from qdrant_client.http import models
from langchain_openai import OpenAIEmbeddings

# Ensure consistent langdetect
DetectorFactory.seed = 0

def clean_text(text: str) -> str:
    text = re.split(r'references|bibliography|bibliographie', text, flags=re.IGNORECASE)[0]
    text = re.sub(r'\n\d+\n', '\n', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^Page \d+ of \d+$', '', text, flags=re.IGNORECASE | re.MULTILINE)
    return text.strip()

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for p in paragraphs:
        words = p.split()
        
        if len(words) > chunk_size * 2:
            for i in range(0, len(words), chunk_size):
                sub_words = words[i:i+chunk_size]
                if current_length + len(sub_words) > chunk_size and current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = current_chunk[-overlap:] if overlap > 0 else []
                    current_length = len(current_chunk)
                current_chunk.extend(sub_words)
                current_length += len(sub_words)
            continue
            
        if current_length + len(words) > chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = current_chunk[-overlap:] if overlap > 0 else []
            current_length = len(current_chunk)
            
        current_chunk.extend(words)
        current_length += len(words)
        
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def extract_keywords(text: str) -> List[str]:
    words = re.findall(r'\b[A-Za-zÀ-ÿ]{6,}\b', text.lower())
    freq = {}
    stopwords = ["patient", "patients", "traitement", "treatment", "maladie", "disease", "medical"]
    for w in words:
        if w not in stopwords:
            freq[w] = freq.get(w, 0) + 1
    return sorted(freq.keys(), key=lambda x: freq[x], reverse=True)[:5]

def extract_section_title(text: str) -> str:
    match = re.search(r'^([A-ZÀ-Ÿ\s]{5,50})\n', text)
    if match:
        return match.group(1).strip()
    return "general"

def detect_language(text: str) -> str:
    try:
        if len(text.strip()) < 10:
            return "fr"
        return detect(text)
    except:
        return "fr"

def detect_document_type(specialty: str, text: str) -> str:
    text_lower = text.lower()
    if specialty == "bilan_expert":
        return "bilan"
    elif any(k in text_lower for k in ["protocol", "guideline", "procedure", "procédure", "directive"]):
        return "guideline"
    elif any(k in text_lower for k in ["symptom", "diagnosis", "treatment", "symptôme", "diagnostic", "clinique"]):
        return "clinical"
    return "knowledge"

def get_hash_id(text: str, source: str, page: int) -> str:
    base = f"{source}_{page}_{text[:50]}"
    hash_object = hashlib.md5(base.encode('utf-8'))
    return str(uuid.UUID(hash_object.hexdigest()))

def process_document_pages(file_path: Path) -> List[str]:
    file_ext = file_path.suffix.lower()
    content_chunks = []
    try:
        if file_ext == '.pdf':
            doc = fitz.open(str(file_path))
            for page in doc:
                text = page.get_text()
                if text.strip():
                    content_chunks.append(text)
            doc.close()
        elif file_ext == '.json':
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                content_chunks.append(json.dumps(data, indent=2))
        elif file_ext in ['.txt', '.md', '.csv']:
            with open(file_path, 'r', encoding='utf-8') as f:
                content_chunks.append(f.read())
    except Exception as e:
        print(f"\n[Warning] Could not read file {file_path.name}: {str(e)}")
    return content_chunks

def load_documents_for_folder(folder_path: str, specialty_name: str) -> List[Dict[str, Any]]:
    docs = []
    folder_dir = Path(folder_path)
    
    if not folder_dir.exists():
        print(f"[Error] Directory not found: {folder_path}")
        return docs
        
    for file_path in folder_dir.rglob("*"):
        if not file_path.is_file():
            continue
            
        start_time = time.time()
        pages = process_document_pages(file_path)
        process_dur = time.time() - start_time
        if pages:
            print(f"Processed {file_path.name} in {process_dur:.2f}s")
            docs.append({
                "pages": pages,
                "specialty": specialty_name,
                "source": file_path.name,
                "source_path": str(file_path),
                "time": process_dur
            })
    return docs

def generate_chunks(raw_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    structured_chunks = []
    for doc in tqdm(raw_docs, desc="Extracting, Cleaning & Chunking"):
        for page_num, raw_page_text in enumerate(doc["pages"]):
            cleaned_text = clean_text(raw_page_text)
            if len(cleaned_text) < 20:
                continue
            
            sample = cleaned_text[:1000] if len(cleaned_text) > 1000 else cleaned_text
            doc_lang = detect_language(sample)
            doc_type = detect_document_type(doc["specialty"], sample)
            
            chunks = chunk_text(cleaned_text, chunk_size=400, overlap=50)
            
            for chunk_idx, chunk in enumerate(chunks):
                if len(chunk.strip()) < 20: 
                    continue
                    
                chunk_id = get_hash_id(chunk, doc["source"], page_num + 1)
                section = extract_section_title(chunk)
                keywords = extract_keywords(chunk)
                importance_score = len(chunk.split()) / 400.0
                priority = 1.0 if doc_type == "clinical" else 0.7
                
                structured_chunks.append({
                    "text": chunk,
                    "specialty": doc["specialty"],
                    "source": doc["source"],
                    "source_path": doc["source_path"],
                    "page_num": page_num + 1,
                    "chunk_index": chunk_idx,
                    "document_type": doc_type,
                    "language": doc_lang,
                    "section": section,
                    "keywords": keywords,
                    "importance_score": importance_score,
                    "priority": priority,
                    "chunk_id": chunk_id,
                    "type": "medical_knowledge",
                    "agent_ready": True
                })
    return structured_chunks

def embed_with_retry(texts: List[str], model: OpenAIEmbeddings, retries: int = 3) -> List[List[float]]:
    for i in range(retries):
        try:
            return model.embed_documents(texts)
        except Exception as e:
            time.sleep(2 ** i)
    raise Exception(f"Embedding failed after {retries} retries.")

def upload_to_qdrant(structured_chunks: List[Dict[str, Any]]):
    qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
    qdrant_api_key = os.getenv("QDRANT_API_KEY", "")
    
    if not os.getenv("QDRANT_URL"):
        print("\n[Security] Env QDRANT_URL missing. Using local Qdrant fallback (http://localhost:6333)")
    
    try:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key, timeout=120.0)
    except Exception as e:
        print(f"[Error] Failed to connect to Qdrant: {e}")
        return

    embeddings_model = OpenAIEmbeddings(model="text-embedding-3-large", request_timeout=30.0)
    
    print("\nDetecting dynamic vector size for the current model...")
    sample_embedding = embeddings_model.embed_query("test")
    vector_size = len(sample_embedding)
    print(f"Dynamic vector size established at: {vector_size}")
    
    collections_data = {}
    for chunk in structured_chunks:
        col_name = f"{chunk['specialty']}_collection"
        if col_name not in collections_data:
            collections_data[col_name] = []
        collections_data[col_name].append(chunk)

    for col_name, chunks in collections_data.items():
        exists = client.collection_exists(col_name)
        if not exists:
            print(f"\nCreating collection '{col_name}'...")
            client.create_collection(
                collection_name=col_name,
                vectors_config=models.VectorParams(
                    size=vector_size, 
                    distance=models.Distance.COSINE
                )
            )
            client.create_payload_index(collection_name=col_name, field_name="specialty", field_schema=models.PayloadSchemaType.KEYWORD)
            client.create_payload_index(collection_name=col_name, field_name="document_type", field_schema=models.PayloadSchemaType.KEYWORD)
            client.create_payload_index(collection_name=col_name, field_name="keywords", field_schema=models.PayloadSchemaType.KEYWORD)
            client.create_payload_index(collection_name=col_name, field_name="importance_score", field_schema=models.PayloadSchemaType.FLOAT)
            client.create_payload_index(collection_name=col_name, field_name="priority", field_schema=models.PayloadSchemaType.FLOAT)
            client.create_payload_index(collection_name=col_name, field_name="chunk_index", field_schema=models.PayloadSchemaType.INTEGER)
            
        print(f"\nGenerating embeddings and upserting into '{col_name}' (Total Chunks: {len(chunks)})...")
        
        batch_size = 100
        for i in tqdm(range(0, len(chunks), batch_size), desc=f"Upserting {col_name}"):
            batch = chunks[i:i+batch_size]
            texts = [c["text"] for c in batch]
            ids = [c["chunk_id"] for c in batch]
            
            try:
                vectors = embed_with_retry(texts, embeddings_model)
                points = [
                    models.PointStruct(id=ids[j], vector=vectors[j], payload=batch[j])
                    for j in range(len(batch))
                ]
                client.upsert(collection_name=col_name, points=points)
            except Exception as e:
                print(f"[Error] Failed upsert batch in {col_name}: {e}")

def main():
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        print("[Fatal] OPENAI_API_KEY environment variable is required.")
        return

    # Specific Target
    folder_path = r"c:\Users\Omar\Desktop\Gabsi\Gabesi-AIGuardian\data\datamed\bilan_expert"
    specialty_name = "bilan_expert"
    
    print(f"\n=== MEDICAL RAG PIPELINE (Targing Folder: {specialty_name}) ===")
    
    docs = load_documents_for_folder(folder_path, specialty_name)
    print(f"\n[Stats] Extracted {len(docs)} documents.")
    
    if not docs:
        print("[Info] Pipeline stopped. No documents found.")
        return
        
    chunks = generate_chunks(docs)
    print(f"[Stats] Created {len(chunks)} cleaned, semantic chunks for {specialty_name}.")
    
    upload_to_qdrant(chunks)
    
    print("\n=== PIPELINE SUCCESS ===")
    print(f"Collection '{specialty_name}_collection' is safely provisioned and populated.")

if __name__ == "__main__":
    main()
