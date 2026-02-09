"""
Süper Basit RAG - Fixed Version
"""
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

print("🚀 Basit RAG Başlıyor!\n")

# 1. Bağlan
qdrant = QdrantClient(host="localhost", port=6333)
model = SentenceTransformer('all-MiniLM-L6-v2')

# 2. Collection oluştur
try:
    qdrant.delete_collection("demo")
except:
    pass

qdrant.create_collection(
    collection_name="demo",
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)
print("✅ Collection oluşturuldu!\n")

# 3. Test dokümanı
docs = [
    "Machine Learning yapay zeka dalıdır. Verilerden öğrenir.",
    "Supervised learning etiketli veri kullanır.",
    "Unsupervised learning etiketsiz veri kullanır.",
    "Deep Learning sinir ağları kullanır.",
    "Python ML için en popüler dildir."
]

# 4. Yükle (ID'leri integer yap!)
points = []
for i, doc in enumerate(docs):
    vector = model.encode(doc).tolist()
    points.append(PointStruct(
        id=i,  # ← Integer ID
        vector=vector,
        payload={"text": doc}
    ))

qdrant.upsert(collection_name="demo", points=points)
print(f"✅ {len(docs)} doküman yüklendi!\n")

# 5. Sorgula
questions = [
    "Machine Learning nedir?",
    "Python neden önemli?",
    "Supervised ve unsupervised farkı ne?"
]

for q in questions:
    print(f"❓ Soru: {q}")
    qv = model.encode(q).tolist()
    results = qdrant.search(collection_name="demo", query_vector=qv, limit=2)
    
    for hit in results:
        print(f"   📄 [{hit.score:.2f}] {hit.payload['text']}")
    print()

print("🎉 RAG Çalışıyor!")
