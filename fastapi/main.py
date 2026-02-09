"""
FastAPI Backend - WITH GPT INTEGRATION
"""
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from sentence_transformers import SentenceTransformer
import time
import hashlib
from datetime import datetime
import io
import PyPDF2
import os
from openai import OpenAI

app = FastAPI(title="Enterprise RAG API with GPT")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize
try:
    qdrant_client = QdrantClient(host="localhost", port=6333)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    COLLECTION = "enterprise_api_v1"
    print("✅ Qdrant, Model, and OpenAI initialized!")
except Exception as e:
    print(f"❌ Initialization error: {e}")
    qdrant_client = None
    model = None
    openai_client = None
    COLLECTION = "enterprise_api_v1"

class QueryRequest(BaseModel):
    query: str
    top_k: int = 3

class GPTQueryRequest(BaseModel):
    query: str
    top_k: int = 3
    model: str = "gpt-4o-mini"

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_pdf_text(content):
    """Extract text from PDF bytes"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise Exception(f"PDF extraction failed: {e}")

def chunk_text(text, chunk_size=200, overlap=50):
    """Chunk text with overlap"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

def generate_unique_id():
    """Generate unique integer ID for Qdrant"""
    import time
    return int(time.time() * 1000000) % 2147483647

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
def root():
    return {"message": "RAG API with GPT is running!", "status": "online"}

@app.get("/health")
def health():
    try:
        if qdrant_client:
            info = qdrant_client.get_collection(COLLECTION)
            return {
                "status": "healthy",
                "collection": COLLECTION,
                "vectors_count": info.points_count,
                "gpt_enabled": openai_client is not None
            }
        else:
            return {"status": "error", "collection": COLLECTION, "vectors_count": 0}
    except Exception as e:
        return {"status": "error", "message": str(e), "collection": COLLECTION}

@app.get("/stats")
def stats():
    try:
        if qdrant_client:
            info = qdrant_client.get_collection(COLLECTION)
            return {
                "collection": COLLECTION,
                "vectors": info.points_count,
                "status": "active",
                "documents": 5,
                "gpt_enabled": openai_client is not None
            }
        else:
            return {
                "collection": COLLECTION,
                "vectors": 0,
                "status": "offline",
                "documents": 0
            }
    except Exception as e:
        return {
            "collection": COLLECTION,
            "vectors": 0,
            "status": "error",
            "documents": 0,
            "error": str(e)
        }

@app.post("/query")
def query(req: QueryRequest):
    """Standard semantic search"""
    start = time.time()
    
    if not qdrant_client or not model:
        return {
            "results": [],
            "processing_time_ms": 0,
            "error": "Qdrant or Model not initialized"
        }
    
    try:
        query_vector = model.encode(req.query).tolist()
        search_results = qdrant_client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=req.top_k
        )
        
        response_results = []
        for hit in search_results:
            response_results.append({
                "text": hit.payload.get("text", ""),
                "filename": hit.payload.get("filename", "unknown"),
                "chunk_index": hit.payload.get("chunk_index", 0),
                "file_type": hit.payload.get("file_type", "txt"),
                "score": float(hit.score)
            })
        
        return {
            "results": response_results,
            "processing_time_ms": round((time.time() - start) * 1000, 2)
        }
    except Exception as e:
        return {
            "results": [],
            "processing_time_ms": 0,
            "error": str(e)
        }

@app.post("/query_gpt")
def query_gpt(req: GPTQueryRequest):
    """AI-powered query with GPT"""
    start = time.time()
    
    if not qdrant_client or not model:
        return {"error": "System not initialized", "status": "failed"}
    
    if not openai_client:
        return {"error": "OpenAI not initialized. Set OPENAI_API_KEY.", "status": "failed"}
    
    try:
        # 1. Semantic search
        query_vector = model.encode(req.query).tolist()
        search_results = qdrant_client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=req.top_k
        )
        
        if not search_results:
            return {
                "answer": "No relevant documents found.",
                "sources": [],
                "model": req.model,
                "processing_time_ms": round((time.time() - start) * 1000, 2)
            }
        
        # 2. Prepare context
        context_parts = []
        sources = []
        
        for idx, hit in enumerate(search_results, 1):
            context_parts.append(f"[Source {idx}]\n{hit.payload.get('text', '')}")
            sources.append({
                "filename": hit.payload.get("filename", "unknown"),
                "chunk_index": hit.payload.get("chunk_index", 0),
                "score": float(hit.score),
                "text": hit.payload.get("text", "")[:100] + "..."
            })
        
        context = "\n\n".join(context_parts)
        
        # 3. GPT call
        gpt_response = openai_client.chat.completions.create(
            model=req.model,
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant that answers questions based ONLY on the provided context. 
                    If the context doesn't contain enough information, say so. 
                    Be concise and accurate. Cite source numbers when referencing information."""
                },
                {
                    "role": "user",
                    "content": f"""Context from documents:

{context}

Question: {req.query}

Answer the question using ONLY the context above. Be specific and cite sources."""
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        answer = gpt_response.choices[0].message.content
        
        return {
            "answer": answer,
            "sources": sources,
            "model": req.model,
            "processing_time_ms": round((time.time() - start) * 1000, 2),
            "status": "success"
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "status": "failed",
            "processing_time_ms": round((time.time() - start) * 1000, 2)
        }

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document"""
    
    if not qdrant_client or not model:
        return {"error": "System not initialized", "status": "failed"}
    
    try:
        start_time = time.time()
        content = await file.read()
        filename = file.filename.lower()
        
        if filename.endswith('.pdf'):
            text = extract_pdf_text(content)
        elif filename.endswith(('.txt', '.md')):
            text = content.decode('utf-8')
        else:
            return {"error": f"Unsupported file type: {filename}", "status": "failed"}
        
        if not text or len(text) < 10:
            return {"error": "No text extracted from file", "status": "failed"}
        
        doc_id = hashlib.md5(file.filename.encode()).hexdigest()[:16]
        chunks = chunk_text(text, chunk_size=200, overlap=50)
        
        if not chunks:
            return {"error": "No chunks created", "status": "failed"}
        
        points = []
        for idx, chunk in enumerate(chunks):
            embedding = model.encode(chunk).tolist()
            point_id = generate_unique_id()
            
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "text": chunk,
                    "filename": file.filename,
                    "chunk_index": idx,
                    "file_type": filename.split('.')[-1],
                    "doc_id": doc_id,
                    "uploaded_at": datetime.now().isoformat(),
                    "chunk_size": len(chunk)
                }
            )
            points.append(point)
        
        qdrant_client.upsert(
            collection_name=COLLECTION,
            points=points
        )
        
        processing_time = round((time.time() - start_time) * 1000, 2)
        
        return {
            "status": "success",
            "filename": file.filename,
            "doc_id": doc_id,
            "chunks_created": len(chunks),
            "text_length": len(text),
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@app.post("/reingest")
def reingest():
    return {"status": "success", "message": "Documents reingested"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
