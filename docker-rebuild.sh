#!/bin/bash
# Docker Compose - Yeniden Build Komutu

# ============================================================================
# YÖNTEM 1: HEM NORMAL DOCKER-COMPOSE HEM DE FULL STACK İÇİN
# ============================================================================

echo "Hangi docker-compose dosyasını build etmek istiyorsunuz?"
echo "1) docker-compose.yml (Tüm stack - MinIO, Spark, Airflow vs.)"
read -p "Seçiminiz (1 veya 2): " choice

if [ "$choice" == "1" ]; then
    FILE="docker-compose.yml"
else
    pass
fi

echo ""
echo "🔨 Build başlatılıyor: $FILE"
echo ""

# Container'ları durdur
echo "1️⃣ Container'lar durduruluyor..."
docker compose -f $FILE down

# Clean build (cache kullanmadan)
echo "2️⃣ Yeniden build ediliyor (cache temizleniyor)..."
docker compose -f $FILE build --no-cache

# Başlat
echo "3️⃣ Container'lar başlatılıyor..."
docker compose -f $FILE up -d

echo ""
echo "✅ İşlem tamamlandı!"
echo ""
echo "📊 Container durumları:"
docker compose -f $FILE ps

echo ""
echo "📝 Logları görmek için:"
echo "   docker compose -f $FILE logs -f fastapi"