cat > ~/rag-pipeline-v1/README.md << 'EOF'
# 🚀 Production RAG System with Apache Iceberg

Enterprise-grade Retrieval-Augmented Generation (RAG) system combining modern data lake architecture with AI-powered semantic search.

---

## 🎯 What We Built
```
✅ Apache Iceberg Data Lake (ACID + Time Travel)
✅ Project Nessie (Git-like Versioning)
✅ Apache Spark (Distributed Processing)
✅ Trino SQL Engine (Query Interface)
✅ Qdrant Vector DB (Semantic Search)
✅ Streamlit + FastAPI (Modern Web UI)
✅ GPT-4o-mini Integration (AI Answers)
✅ MinIO S3 Storage (Object Store)
```

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────┐
│                 WEB INTERFACE                           │
│  ┌──────────────┐         ┌──────────────┐            │
│  │  Streamlit   │────────▶│   FastAPI    │            │
│  │  (Port 8501) │         │  (Port 8001) │            │
│  └──────────────┘         └──────────────┘            │
│         │                         │                     │
│         │                         ▼                     │
│         │                  ┌──────────────┐            │
│         │                  │   GPT-4o     │            │
│         │                  │  (AI Layer)  │            │
│         │                  └──────────────┘            │
│         ▼                         │                     │
│  ┌──────────────┐                │                     │
│  │    Qdrant    │◀───────────────┘                     │
│  │  Vector DB   │                                       │
│  │ (408 vectors)│                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│              DATA LAKE LAYER                            │
│  ┌──────────────┐         ┌──────────────┐            │
│  │    Trino     │────────▶│   Iceberg    │            │
│  │ SQL Engine   │         │  Data Lake   │            │
│  │ (Port 8090)  │         │   + Nessie   │            │
│  └──────────────┘         └──────────────┘            │
│         │                         │                     │
│         │                         ▼                     │
│         │                  ┌──────────────┐            │
│         │                  │    MinIO     │            │
│         └─────────────────▶│  S3 Storage  │            │
│                             └──────────────┘            │
└─────────────────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│           PROCESSING LAYER                              │
│  ┌──────────────┐         ┌──────────────┐            │
│  │Spark Master  │────────▶│Spark Worker  │            │
│  │ (Port 8081)  │         │ (2 cores)    │            │
│  └──────────────┘         └──────────────┘            │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- 8GB RAM minimum
- Ports: 6333, 8001, 8090, 8501, 9000, 9001, 19120

### 1. Start Services
```bash
cd ~/rag-pipeline-v1
docker-compose up -d
```

### 2. Initialize MinIO
```bash
docker exec -it minio sh
mc alias set local http://localhost:9000 admin minioadmin123
mc mb local/warehouse
mc ls local
exit
```

### 3. Create Iceberg Tables
```bash
docker exec -it spark-master bash -c '
export AWS_REGION=us-east-1 && \
/opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark-jars/iceberg-spark-runtime-3.5_2.12-1.4.3.jar,/opt/spark-jars/nessie-spark-extensions-3.5_2.12-0.74.0.jar,/opt/spark-jars/bundle-2.20.18.jar,/opt/spark-jars/hadoop-aws-3.3.4.jar \
  /opt/spark-apps/iceberg-integration/scripts/01_create_iceberg_tables.py
'
```

### 4. Load Sample Data
```bash
docker exec -it spark-master bash -c '
export AWS_REGION=us-east-1 && \
/opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark-jars/iceberg-spark-runtime-3.5_2.12-1.4.3.jar,/opt/spark-jars/nessie-spark-extensions-3.5_2.12-0.74.0.jar,/opt/spark-jars/bundle-2.20.18.jar,/opt/spark-jars/hadoop-aws-3.3.4.jar \
  /opt/spark-apps/iceberg-integration/scripts/02_load_sample_data.py
'
```

### 5. Start Web UI & API
```bash
# Terminal 1: FastAPI
cd ~/rag-pipeline-v1/fastapi
export OPENAI_API_KEY="your-key-here"
python main.py

# Terminal 2: Streamlit
cd ~/rag-pipeline-v1/streamlit-ui
streamlit run app.py
```

---

## 🌐 Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| **Streamlit UI** | http://localhost:8501 | - |
| **FastAPI Docs** | http://localhost:8001/docs | - |
| **Trino UI** | http://localhost:8090 | - |
| **MinIO Console** | http://localhost:9001 | admin / minioadmin123 |
| **Spark Master** | http://localhost:8081 | - |
| **Qdrant Dashboard** | http://localhost:6333/dashboard | - |
| **Nessie API** | http://localhost:19120/api/v1/config | - |

---

## 📊 Data Lake Structure

### Iceberg Tables
```sql
-- Database: iceberg.rag_data_lake

-- Table 1: raw_documents
doc_id           STRING
filename         STRING
content          STRING
file_type        STRING
file_size        BIGINT
ingestion_date   DATE
-- PARTITIONED BY: days(ingestion_date)

-- Table 2: document_chunks
chunk_id         STRING
doc_id           STRING
chunk_index      INT
chunk_text       STRING
chunk_size       INT
created_at       TIMESTAMP
-- PARTITIONED BY: doc_id
```

### Query Examples (Trino)
```sql
-- View all documents
SELECT * FROM iceberg.rag_data_lake.raw_documents;

-- Count chunks per document
SELECT 
    filename,
    COUNT(*) as num_chunks
FROM iceberg.rag_data_lake.document_chunks c
JOIN iceberg.rag_data_lake.raw_documents d
  ON c.doc_id = d.doc_id
GROUP BY filename;

-- Time Travel (see old versions)
SELECT * FROM iceberg.rag_data_lake.raw_documents 
FOR SYSTEM_TIME AS OF TIMESTAMP '2026-02-08 10:00:00';
```

---

## 🔍 RAG Features

### 1. Document Upload
- **Formats**: PDF, TXT, MD
- **Processing**: Automatic chunking (200 chars, 50 overlap)
- **Storage**: Dual (Iceberg + Qdrant)

### 2. Semantic Search
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Latency**: <70ms
- **Similarity**: Cosine distance

### 3. AI-Powered Answers
- **Model**: GPT-4o-mini
- **Response**: ~2 seconds
- **Citations**: Source tracking

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **UI** | Streamlit | Web interface |
| **API** | FastAPI | REST endpoints |
| **AI** | GPT-4o-mini | Natural language answers |
| **Vector DB** | Qdrant | Semantic search |
| **Data Lake** | Iceberg + Nessie | ACID tables + versioning |
| **SQL Engine** | Trino | Query interface |
| **Processing** | Spark 3.5.0 | Distributed computing |
| **Storage** | MinIO | S3-compatible object store |
| **Metadata** | PostgreSQL | System metadata |

---

## 🔧 Configuration

### DBeaver Connection (Trino)
```
Host: localhost
Port: 8090
Database: iceberg
Schema: rag_data_lake
Username: trino
Password: (leave empty)

Driver Properties:
  SSL: false
```

### OpenAI API Key
```bash
export OPENAI_API_KEY="sk-proj-..."
```

---

## 📈 Performance
```
Documents:       4+
Chunks:          408 vectors
Query Latency:   32-70ms
AI Response:     ~2000ms
Collection:      enterprise_api_v1
Status:          ACTIVE ✅
```

---

## 🐛 Troubleshooting

### Nessie Connection Error
```bash
# Check if Nessie is running
docker ps | grep nessie

# Check logs
docker logs nessie

# Restart if needed
docker-compose restart nessie
```

### Tables Not Found
```bash
# Recreate tables
docker exec -it spark-master bash -c '
export AWS_REGION=us-east-1 && \
/opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --jars /opt/spark-jars/iceberg-spark-runtime-3.5_2.12-1.4.3.jar,/opt/spark-jars/nessie-spark-extensions-3.5_2.12-0.74.0.jar,/opt/spark-jars/bundle-2.20.18.jar,/opt/spark-jars/hadoop-aws-3.3.4.jar \
  /opt/spark-apps/iceberg-integration/scripts/01_create_iceberg_tables.py
'
```

### GPT Quota Exceeded
```bash
# Add credits at platform.openai.com
# Minimum: $5 (33,000+ queries)
```

---

## 📚 Documentation

- [Architecture Diagram](./ARCHITECTURE.md)
- [API Documentation](http://localhost:8001/docs)
- [Iceberg Docs](https://iceberg.apache.org/)
- [Nessie Docs](https://projectnessie.org/)
- [Trino Docs](https://trino.io/)

---

## 🎯 Roadmap

- [ ] Batch document upload
- [ ] Advanced filtering
- [ ] Multi-language support
- [ ] Authentication & RBAC
- [ ] Analytics dashboard
- [ ] Model fine-tuning

---

## 📄 License

MIT

---

**Version**: 2.0  
**Last Updated**: February 9, 2026  
**Status**: Production Ready 
by Şule Akçay

