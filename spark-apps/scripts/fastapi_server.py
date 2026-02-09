"""
Enterprise RAG - FastAPI Backend
Production-ready REST API
"""
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from enterprise_rag import EnterpriseRAG
from datetime import datetime
import uvicorn

# Initialize FastAPI
app = FastAPI(
    title="Enterprise RAG API",
    description="Production-grade RAG system with document management",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG system
rag_system = None

# Models
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class QueryResponse(BaseModel):
    query: str
    results: List[dict]
    timestamp: str
    processing_time_ms: float

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    collection: str
    vectors_count: Optional[int] = None

class StatsResponse(BaseModel):
    collection: str
    documents: int
    chunks: int
    vectors: int
    status: str

# Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize RAG system on startup"""
    global rag_system
    print("🚀 Starting Enterprise RAG API...")
    rag_system = EnterpriseRAG(collection_name="enterprise_api_v1")
    print("✅ RAG system initialized!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Enterprise RAG API v1.0",
        "status": "online",
        "endpoints": {
            "health": "/health",
            "query": "/query",
            "stats": "/stats",
            "reingest": "/reingest",
            "docs": "/docs"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        stats = rag_system.get_stats()
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            collection=stats['collection'],
            vectors_count=stats.get('vectors_count', 0)
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Query the RAG system"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        start_time = datetime.now()
        
        # Search
        results = rag_system.search(request.query, request.top_k)
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return QueryResponse(
            query=request.query,
            results=results,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=round(processing_time, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """Get system statistics"""
    try:
        stats = rag_system.get_stats()
        
        return StatsResponse(
            collection=stats['collection'],
            documents=0,  # TODO: Track this
            chunks=0,     # TODO: Track this
            vectors=stats.get('vectors_count', 0),
            status=stats['status']
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats failed: {str(e)}")

@app.post("/reingest")
async def reingest_documents():
    """Re-ingest all documents"""
    try:
        # Setup collection
        rag_system.setup_collection()
        
        # Ingest
        stats = rag_system.ingest_documents()
        
        return {
            "status": "success",
            "message": "Documents re-ingested successfully",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reingest failed: {str(e)}")

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload a new document"""
    # TODO: Implement file upload
    return {
        "status": "not_implemented",
        "message": "File upload coming soon",
        "filename": file.filename
    }

# Run server
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🏢 ENTERPRISE RAG API SERVER")
    print("=" * 70)
    print("\n📡 Starting server on http://0.0.0.0:8000")
    print("📚 API docs available at http://0.0.0.0:8000/docs")
    print("\n" + "=" * 70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
