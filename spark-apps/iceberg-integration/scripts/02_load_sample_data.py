"""
ADIM 2: Örnek Veri Yükle
Big Data Engineer: Data Ingestion
"""
import os
os.environ['AWS_REGION'] = 'us-east-1'

from pyspark.sql import SparkSession
from pyspark.sql import Row
from datetime import datetime, date
import hashlib

print("="*70)
print("📊 DATA INGESTION - BIG DATA ENGINEER")
print("="*70)
print()

# ============================================================================
# SPARK SESSION
# ============================================================================
print("🔧 Creating Spark Session...")

spark = SparkSession.builder \
    .appName("Load Sample Data") \
    .master("spark://spark-master:7077") \
    .config("spark.driver.memory", "2g") \
    .config("spark.executor.memory", "2g") \
    .config("spark.sql.extensions", "org.apache.iceberg.spark.extensions.IcebergSparkSessionExtensions,org.projectnessie.spark.extensions.NessieSparkSessionExtensions") \
    .config("spark.sql.catalog.nessie", "org.apache.iceberg.spark.SparkCatalog") \
    .config("spark.sql.catalog.nessie.uri", "http://nessie:19120/api/v1") \
    .config("spark.sql.catalog.nessie.ref", "main") \
    .config("spark.sql.catalog.nessie.catalog-impl", "org.apache.iceberg.nessie.NessieCatalog") \
    .config("spark.sql.catalog.nessie.warehouse", "s3a://warehouse") \
    .config("spark.sql.catalog.nessie.io-impl", "org.apache.iceberg.aws.s3.S3FileIO") \
    .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") \
    .config("spark.hadoop.fs.s3a.access.key", "admin") \
    .config("spark.hadoop.fs.s3a.secret.key", "minioadmin123") \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider") \
    .config("spark.sql.catalog.nessie.s3.endpoint", "http://minio:9000") \
    .config("spark.sql.catalog.nessie.s3.access-key-id", "admin") \
    .config("spark.sql.catalog.nessie.s3.secret-access-key", "minioadmin123") \
    .config("spark.sql.catalog.nessie.s3.path-style-access", "true") \
    .getOrCreate()

print("✅ Spark Session created!")
print()

# ============================================================================
# SAMPLE DOCUMENTS
# ============================================================================
print("="*70)
print("📄 STEP 1: Load Sample Documents")
print("="*70)

documents = [
    {
        "filename": "machine_learning_intro.md",
        "content": """Machine Learning is a subset of Artificial Intelligence that enables computers to learn from data. 
        There are three main types: supervised learning (with labeled data), unsupervised learning (finding patterns), 
        and reinforcement learning (learning through rewards). Popular algorithms include Linear Regression, 
        Decision Trees, Neural Networks, and Support Vector Machines.""",
        "file_type": "md"
    },
    {
        "filename": "apache_iceberg_guide.md",
        "content": """Apache Iceberg is an open table format for huge analytic datasets. It provides ACID transactions, 
        time travel queries, and schema evolution. Iceberg uses hidden partitioning and snapshot isolation for 
        concurrent writes. It works seamlessly with Spark, Flink, Trino, and other query engines.""",
        "file_type": "md"
    },
    {
        "filename": "vector_databases.txt",
        "content": """Vector databases store high-dimensional embeddings for semantic search. They use distance metrics 
        like cosine similarity and Euclidean distance. Popular vector databases include Qdrant, Pinecone, Weaviate, 
        and Milvus. They are essential for RAG (Retrieval Augmented Generation) applications.""",
        "file_type": "txt"
    },
    {
        "filename": "big_data_engineering.txt",
        "content": """Big Data Engineering involves designing and building systems to process large-scale data. 
        Key technologies include Apache Spark for distributed processing, Apache Kafka for streaming, 
        Apache Airflow for orchestration, and data lakes using formats like Iceberg and Delta Lake. 
        Data engineers ensure data quality, reliability, and scalability.""",
        "file_type": "txt"
    }
]

# Create document rows
doc_rows = []
for doc in documents:
    doc_id = hashlib.md5(doc['filename'].encode()).hexdigest()[:16]
    doc_rows.append(Row(
        doc_id=doc_id,
        filename=doc['filename'],
        content=doc['content'],
        file_type=doc['file_type'],
        file_size=len(doc['content']),
        ingestion_date=date.today()
    ))

# Write to Iceberg
df_docs = spark.createDataFrame(doc_rows)
df_docs.writeTo("nessie.rag_data_lake.raw_documents").append()

print(f"✅ Loaded {len(doc_rows)} documents!")
print()

# ============================================================================
# CREATE CHUNKS
# ============================================================================
print("="*70)
print("✂️  STEP 2: Create Document Chunks")
print("="*70)

def chunk_text(text, chunk_size=200, overlap=50):
    """Simple chunking with overlap"""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += (chunk_size - overlap)
    return chunks

# Create chunks
chunk_rows = []
for doc in documents:
    doc_id = hashlib.md5(doc['filename'].encode()).hexdigest()[:16]
    chunks = chunk_text(doc['content'], chunk_size=200, overlap=50)
    
    for idx, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{doc_id}-{idx}".encode()).hexdigest()[:16]
        chunk_rows.append(Row(
            chunk_id=chunk_id,
            doc_id=doc_id,
            chunk_index=idx,
            chunk_text=chunk,
            chunk_size=len(chunk),
            created_at=datetime.now()
        ))

# Write to Iceberg
df_chunks = spark.createDataFrame(chunk_rows)
df_chunks.writeTo("nessie.rag_data_lake.document_chunks").append()

print(f"✅ Created {len(chunk_rows)} chunks!")
print()

# ============================================================================
# VERIFY DATA
# ============================================================================
print("="*70)
print("🔍 STEP 3: Verify Data")
print("="*70)

print("\n📊 Documents:")
spark.sql("SELECT doc_id, filename, file_size FROM nessie.rag_data_lake.raw_documents").show(truncate=False)

print("\n✂️  Chunks (first 10):")
spark.sql("""
    SELECT chunk_id, doc_id, chunk_index, chunk_size, LEFT(chunk_text, 50) as preview
    FROM nessie.rag_data_lake.document_chunks
    ORDER BY doc_id, chunk_index
    LIMIT 10
""").show(truncate=False)

print("\n📈 Summary:")
doc_count = spark.sql("SELECT COUNT(*) as cnt FROM nessie.rag_data_lake.raw_documents").collect()[0]['cnt']
chunk_count = spark.sql("SELECT COUNT(*) as cnt FROM nessie.rag_data_lake.document_chunks").collect()[0]['cnt']
print(f"   Total Documents: {doc_count}")
print(f"   Total Chunks: {chunk_count}")

print()
print("="*70)
print("✅ DATA INGESTION COMPLETE!")
print("="*70)

spark.stop()
print("\n👋 Done!")
