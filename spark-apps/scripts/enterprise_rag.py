"""
Enterprise RAG System
- Document loading
- Smart chunking  
- Vector storage (Qdrant)
- Semantic search
- Metadata tracking
"""
from document_loader import DocumentLoader, SmartChunker
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import List, Dict
from datetime import datetime
import json

class EnterpriseRAG:
    """Production-grade RAG system"""
    
    def __init__(
        self,
        collection_name: str = "enterprise_docs",
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        embedding_model: str = "all-MiniLM-L6-v2"
    ):
        self.collection_name = collection_name
        
        # Initialize components
        print("🔧 Initializing Enterprise RAG System...")
        self.qdrant = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.model = SentenceTransformer(embedding_model)
        self.loader = DocumentLoader()
        self.chunker = SmartChunker(chunk_size=500, overlap=100)
        print("✅ Components initialized!\n")
    
    def setup_collection(self):
        """Create or recreate Qdrant collection"""
        print(f"🗄️  Setting up collection: {self.collection_name}")
        
        # Delete if exists
        try:
            self.qdrant.delete_collection(self.collection_name)
            print("   - Deleted old collection")
        except:
            pass
        
        # Create new
        self.qdrant.create_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(
                size=384,  # all-MiniLM-L6-v2 dimension
                distance=Distance.COSINE
            )
        )
        print("✅ Collection created!\n")
    
    def ingest_documents(self) -> Dict:
        """Load, chunk, and index all documents"""
        print("=" * 70)
        print("📥 DOCUMENT INGESTION PIPELINE")
        print("=" * 70)
        
        # Step 1: Load documents
        print("\n🔹 STEP 1: Loading Documents")
        print("-" * 70)
        documents = self.loader.load_all()
        print(f"✅ Loaded {len(documents)} documents\n")
        
        if not documents:
            print("⚠️  No documents found!")
            return {"status": "error", "message": "No documents"}
        
        # Step 2: Chunk documents
        print("🔹 STEP 2: Chunking Documents")
        print("-" * 70)
        all_chunks = []
        for doc in documents:
            chunks = self.chunker.chunk_document(doc)
            all_chunks.extend(chunks)
            print(f"   📄 {doc.filename}: {len(chunks)} chunks")
        print(f"✅ Created {len(all_chunks)} chunks\n")
        
        # Step 3: Generate embeddings
        print("🔹 STEP 3: Generating Embeddings")
        print("-" * 70)
        points = []
        for i, chunk in enumerate(all_chunks):
            if i % 10 == 0:
                print(f"   Processing: {i}/{len(all_chunks)}", end='\r')
            
            # Generate embedding
            vector = self.model.encode(chunk['chunk_text']).tolist()
            
            # Create point
            points.append(PointStruct(
                id=i,
                vector=vector,
                payload={
                    'chunk_id': chunk['chunk_id'],
                    'doc_id': chunk['doc_id'],
                    'chunk_index': chunk['chunk_index'],
                    'text': chunk['chunk_text'],
                    'filename': chunk['doc_filename'],
                    'file_type': chunk['doc_type'],
                    'chunk_size': chunk['chunk_size'],
                    'strategy': chunk['chunking_strategy'],
                    'indexed_at': datetime.now().isoformat()
                }
            ))
        print(f"\n✅ Generated {len(points)} embeddings\n")
        
        # Step 4: Upload to Qdrant
        print("🔹 STEP 4: Uploading to Qdrant")
        print("-" * 70)
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points
        )
        print(f"✅ Uploaded {len(points)} vectors to Qdrant\n")
        
        # Summary
        print("=" * 70)
        print("✅ INGESTION COMPLETE!")
        print("=" * 70)
        
        stats = {
            'status': 'success',
            'documents': len(documents),
            'chunks': len(all_chunks),
            'vectors': len(points),
            'collection': self.collection_name,
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"""
📊 Statistics:
   - Documents processed: {stats['documents']}
   - Chunks created: {stats['chunks']}
   - Vectors indexed: {stats['vectors']}
   - Collection: {stats['collection']}
        """)
        
        return stats
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for similar documents"""
        # Generate query embedding
        query_vector = self.model.encode(query).tolist()
        
        # Search in Qdrant
        results = self.qdrant.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=top_k
        )
        
        # Format results
        formatted = []
        for hit in results:
            formatted.append({
                'score': hit.score,
                'text': hit.payload['text'],
                'filename': hit.payload['filename'],
                'chunk_index': hit.payload['chunk_index'],
                'file_type': hit.payload['file_type']
            })
        
        return formatted
    
    def query(self, question: str, top_k: int = 3):
        """User-friendly query interface"""
        print("\n" + "=" * 70)
        print(f"❓ QUERY: {question}")
        print("=" * 70)
        
        results = self.search(question, top_k)
        
        print(f"\n📊 Found {len(results)} relevant chunks:\n")
        
        for i, result in enumerate(results, 1):
            print(f"🔹 Result {i} [Score: {result['score']:.3f}]")
            print(f"   📄 Source: {result['filename']} (chunk {result['chunk_index']})")
            print(f"   📝 {result['text'][:200]}...")
            print()
        
        return results
    
    def get_stats(self):
        """Get collection statistics"""
        info = self.qdrant.get_collection(self.collection_name)
        return {
            'collection': self.collection_name,
            'vectors_count': info.vectors_count,
            'indexed_vectors': info.indexed_vectors_count,
            'status': info.status
        }


def main():
    """Main execution"""
    print("\n" + "🏢" * 35)
    print("       ENTERPRISE RAG SYSTEM v1.0")
    print("🏢" * 35 + "\n")
    
    # Initialize
    rag = EnterpriseRAG(collection_name="enterprise_docs_v1")
    
    # Setup collection
    rag.setup_collection()
    
    # Ingest documents
    stats = rag.ingest_documents()
    
    # Example queries
    print("\n" + "🔍" * 35)
    print("       EXAMPLE QUERIES")
    print("🔍" * 35)
    
    queries = [
        "Machine Learning nedir?",
        "Iceberg ne işe yarar?",
        "Vector database nasıl çalışır?"
    ]
    
    for query in queries:
        rag.query(query, top_k=3)
        input("Press Enter for next query...")
    
    # Final stats
    print("\n" + "=" * 70)
    print("📊 FINAL STATISTICS")
    print("=" * 70)
    final_stats = rag.get_stats()
    print(json.dumps(final_stats, indent=2))
    
    print("\n✅ Enterprise RAG System Ready!")
    print("=" * 70)


if __name__ == "__main__":
    main()
