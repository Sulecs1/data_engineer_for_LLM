"""
ADIM 1: Iceberg Tablolarını Oluştur
Big Data Engineer: Data Lake Setup
"""
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from datetime import datetime

print("="*70)
print("🏗️  ICEBERG TABLE CREATION - BIG DATA ENGINEER")
print("="*70)
print()

# ============================================================================
# SPARK SESSION (Iceberg + Nessie + MinIO)
# ============================================================================
print("🔧 Creating Spark Session with Iceberg...")

spark = SparkSession.builder \
    .appName("Iceberg Table Setup") \
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
print(f"   Spark Version: {spark.version}")
print()

# ============================================================================
# CREATE DATABASE
# ============================================================================
print("="*70)
print("📦 STEP 1: Create Database")
print("="*70)

try:
    spark.sql("CREATE DATABASE IF NOT EXISTS nessie.rag_data_lake")
    print("✅ Database 'nessie.rag_data_lake' created!")
except Exception as e:
    print(f"⚠️  Database might exist: {e}")

print()

# ============================================================================
# TABLE 1: RAW_DOCUMENTS
# ============================================================================
print("="*70)
print("📄 STEP 2: Create RAW_DOCUMENTS Table")
print("="*70)
print("Purpose: Store original documents with full history")
print("Big Data: ACID transactions, partitioning, snapshots")
print()

spark.sql("""
CREATE TABLE IF NOT EXISTS nessie.rag_data_lake.raw_documents (
    doc_id STRING,
    filename STRING,
    content STRING,
    file_type STRING,
    file_size BIGINT,
    ingestion_date DATE
)
USING iceberg
PARTITIONED BY (days(ingestion_date))
""")

print("✅ Table 'raw_documents' created!")
print()

# ============================================================================
# TABLE 2: DOCUMENT_CHUNKS  
# ============================================================================
print("="*70)
print("✂️  STEP 3: Create DOCUMENT_CHUNKS Table")
print("="*70)

spark.sql("""
CREATE TABLE IF NOT EXISTS nessie.rag_data_lake.document_chunks (
    chunk_id STRING,
    doc_id STRING,
    chunk_index INT,
    chunk_text STRING,
    chunk_size INT,
    created_at TIMESTAMP
)
USING iceberg
PARTITIONED BY (doc_id)
""")

print("✅ Table 'document_chunks' created!")
print()

# ============================================================================
# VERIFY TABLES
# ============================================================================
print("="*70)
print("🔍 STEP 4: Verify Tables")
print("="*70)

tables = spark.sql("SHOW TABLES IN nessie.rag_data_lake").collect()
print(f"\n✅ Created {len(tables)} tables:\n")
for table in tables:
    print(f"   📊 {table.tableName}")

print()
print("="*70)
print("✅ ICEBERG TABLES CREATED!")
print("="*70)

spark.stop()
print("\n👋 Done!")
