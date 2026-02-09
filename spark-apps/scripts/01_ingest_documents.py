"""
Document Ingestion Script
Uploads raw documents to Iceberg
"""
from pyspark.sql import SparkSession, Row
from datetime import datetime
import hashlib

def ingest_documents(spark, docs):
    """Ingest documents into raw_documents table"""
    
    print("📥 Ingesting documents...")
    
    for doc in docs:
        doc_id = hashlib.md5(doc['source'].encode()).hexdigest()[:16]
        
        spark.createDataFrame([Row(
            doc_id=doc_id,
            title=doc['title'],
            content=doc['content'],
            source=doc['source'],
            ingested_at=datetime.now()
        )]).write.mode("append").insertInto("nessie.rag.raw_documents")
    
    print(f"✅ {len(docs)} documents ingested!")
    
    # Show results
    spark.sql("SELECT doc_id, title, source FROM nessie.rag.raw_documents").show(truncate=False)

if __name__ == "__main__":
    docs = [
        {
            "title": "Machine Learning Basics",
            "content": "Machine Learning is a subset of AI...",
            "source": "ml-basics.md"
        }
    ]
    ingest_documents(spark, docs)
