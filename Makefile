.PHONY: help up down restart logs ps clean health init-airflow

# Varsayılan hedef
help:
	@echo "========================================="
	@echo "RAG Pipeline - Makefile Komutları"
	@echo "========================================="
	@echo ""
	@echo "make up            - Tüm servisleri başlat"
	@echo "make down          - Tüm servisleri durdur"
	@echo "make restart       - Tüm servisleri yeniden başlat"
	@echo "make logs          - Tüm logları göster"
	@echo "make ps            - Servislerin durumunu göster"
	@echo "make health        - Health check yap"
	@echo "make init-airflow  - Airflow'u initialize et"
	@echo "make clean         - Tüm verileri sil (DİKKAT!)"
	@echo ""
	@echo "Servis Spesifik:"
	@echo "make logs-minio    - MinIO logları"
	@echo "make logs-spark    - Spark logları"
	@echo "make logs-airflow  - Airflow logları"
	@echo ""

# Servisleri başlat
up:
	@echo "🚀 Servisler başlatılıyor..."
	docker-compose up -d
	@echo ""
	@echo "✅ Servisler başlatıldı!"
	@echo ""
	@echo "📊 Erişim Bilgileri:"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "MinIO Console:    http://localhost:9001"
	@echo "Spark Master UI:  http://localhost:8080"
	@echo "Airflow UI:       http://localhost:8082"
	@echo "Qdrant Dashboard: http://localhost:6333/dashboard"
	@echo "Nessie API:       http://localhost:19120/api/v1"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "⚠️  İlk çalıştırmada Airflow'u initialize edin:"
	@echo "   make init-airflow"
	@echo ""

# Servisleri durdur
down:
	@echo "🛑 Servisler durduruluyor..."
	docker-compose down
	@echo "✅ Servisler durduruldu!"

# Servisleri yeniden başlat
restart:
	@echo "🔄 Servisler yeniden başlatılıyor..."
	docker-compose restart
	@echo "✅ Servisler yeniden başlatıldı!"

# Logları göster
logs:
	docker-compose logs -f

# Sadece MinIO logları
logs-minio:
	docker-compose logs -f minio

# Sadece Spark logları
logs-spark:
	docker-compose logs -f spark-master spark-worker

# Sadece Airflow logları
logs-airflow:
	docker-compose logs -f airflow-webserver airflow-scheduler

# Sadece Nessie logları
logs-nessie:
	docker-compose logs -f nessie

# Servislerin durumu
ps:
	@echo "📊 Servis Durumları:"
	@docker-compose ps
	@echo ""

# Health check
health:
	@echo "🏥 Servis Sağlık Kontrolü"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo -n "MinIO:     "
	@curl -sf http://localhost:9000/minio/health/live > /dev/null && echo "✅ Healthy" || echo "❌ Down"
	@echo -n "Nessie:    "
	@curl -sf http://localhost:19120/api/v1/config > /dev/null && echo "✅ Healthy" || echo "❌ Down"
	@echo -n "Spark:     "
	@curl -sf http://localhost:8080 > /dev/null && echo "✅ Healthy" || echo "❌ Down"
	@echo -n "Qdrant:    "
	@curl -sf http://localhost:6333/health > /dev/null && echo "✅ Healthy" || echo "❌ Down"
	@echo -n "Airflow:   "
	@curl -sf http://localhost:8082/health > /dev/null && echo "✅ Healthy" || echo "❌ Down"
	@echo -n "PostgreSQL:"
	@docker-compose exec -T postgres pg_isready -U airflow > /dev/null 2>&1 && echo "✅ Healthy" || echo "❌ Down"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Airflow'u initialize et
init-airflow:
	@echo "🔧 Airflow initialize ediliyor..."
	@echo ""
	@echo "1. Database initialize..."
	docker-compose exec -T airflow-webserver airflow db init
	@echo ""
	@echo "2. Admin kullanıcısı oluşturuluyor..."
	docker-compose exec -T airflow-webserver airflow users create \
		--username admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com \
		--password admin
	@echo ""
	@echo "✅ Airflow hazır!"
	@echo "   URL: http://localhost:8082"
	@echo "   Login: admin / admin"

# Temizlik (tüm veriler silinir!)
clean:
	@echo "⚠️  DİKKAT: Tüm veriler silinecek!"
	@echo "  - MinIO data"
	@echo "  - PostgreSQL data"
	@echo "  - Qdrant data"
	@echo "  - Airflow logs"
	@echo ""
	@read -p "Devam etmek istediğinize emin misiniz? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "✅ Tüm veriler silindi!"; \
		echo "⚠️  Yeniden başlatmak için: make up && make init-airflow"; \
	else \
		echo "❌ İşlem iptal edildi."; \
	fi

# Dizin yapısını oluştur
setup-dirs:
	@echo "📁 Dizinler oluşturuluyor..."
	mkdir -p spark-apps
	mkdir -p data
	mkdir -p airflow/dags
	mkdir -p airflow/logs
	mkdir -p airflow/plugins
	@echo "✅ Dizinler hazır!"