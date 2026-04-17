import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from qdrant_client import QdrantClient
from app.api.routes import router
from app.config import settings

from contextlib import asynccontextmanager

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=60,
            prefer_grpc=False
        )
        count = client.count(collection_name=settings.collection_name).count
        logger.info(f"Connected to Qdrant. Collection '{settings.collection_name}' has {count} points.")
    except Exception as e:
        logger.error(f"Failed to connect to Qdrant on startup: {str(e)}")
    yield

app = FastAPI(
    title="Gabesi AIGuardian API",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
