"""
Chunking Script
Creates chunks from raw documents
"""
from pyspark.sql import Row
from datetime import datetime
import hashlib

def chunk_text(text, chunk_size=200, overlap=50):
    """Fixed-size chunking with overlap"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())
        start += (chunk_size - overlap)
    return chunks

def create_chunks(spark, chunking_strategy="fixed-200-overlap-50"):
    """Create chunks from raw documents"""
    
    print(f"✂️  Creating chunks with strategy: {chunking_strategy}")
    
    docs_df = spark.sql("SELECT * FROM nessie.rag.raw_documents").collect()
    
    chunk_rows = []
    for doc in docs_df:
        chunks = chunk_text(doc.content, chunk_size=200, overlap=50)
        
        for idx, chunk in enumerate(chunks):
            chunk_id = hashlib.md5(f"{doc.doc_id}-{idx}".encode()).hexdigest()[:16]
            chunk_rows.append(Row(
                chunk_id=chunk_id,
                doc_id=doc.doc_id,
                chunk_index=idx,
                chunk_text=chunk,
                chunk_size=len(chunk),
                chunking_strategy=chunking_strategy,
                created_at=datetime.now()
            ))
    
    spark.createDataFrame(chunk_rows).write.mode("overwrite").insertInto("nessie.rag.document_chunks")
    
    print(f"✅ {len(chunk_rows)} chunks created!")
    
    spark.sql("""
    SELECT doc_id, chunk_index, chunk_size, LEFT(chunk_text, 50) as preview 
    FROM nessie.rag.document_chunks 
    ORDER BY doc_id, chunk_index
    """).show(truncate=False)
    
    snapshot_id = spark.sql("""
    SELECT snapshot_id 
    FROM nessie.rag.document_chunks.snapshots 
    ORDER BY committed_at DESC LIMIT 1
    """).collect()[0][0]
    
    print(f"📸 Snapshot ID: {snapshot_id}")
    return snapshot_id

if __name__ == "__main__":
    snapshot = create_chunks(spark)
