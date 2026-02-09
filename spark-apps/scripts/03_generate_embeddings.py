"""
Embedding Generation Script
Creates embedding metadata
"""
from pyspark.sql import Row
from datetime import datetime
import random

def fake_embedding(text, dimension=384):
    """Demo embedding"""
    random.seed(hash(text))
    return [random.random() for _ in range(dimension)]

def generate_embeddings(spark, embedding_model="fake-bert-base-384", dimension=384):
    """Generate embeddings for all chunks"""
    
    print(f"🔢 Generating embeddings with model: {embedding_model}")
    
    chunks_df = spark.sql("SELECT * FROM nessie.rag.document_chunks").collect()
    
    embedding_rows = []
    for chunk in chunks_df:
        embedding_vector = fake_embedding(chunk.chunk_text, dimension=dimension)
        
        embedding_rows.append(Row(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            embedding_model=embedding_model,
            vector_dimension=dimension,
            created_at=datetime.now(),
            snapshot_id=0
        ))
    
    spark.createDataFrame(embedding_rows).write.mode("overwrite").insertInto("nessie.rag.embeddings_metadata")
    
    print(f"✅ {len(embedding_rows)} embeddings generated!")
    
    spark.sql("""
    SELECT chunk_id, doc_id, embedding_model, vector_dimension 
    FROM nessie.rag.embeddings_metadata
    """).show(truncate=False)

if __name__ == "__main__":
    generate_embeddings(spark)
