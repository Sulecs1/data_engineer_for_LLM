FROM python:3.11-slim

WORKDIR /app

# Gerekli paketler
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    uvicorn[standard]==0.24.0 \
    pydantic==2.5.0 \
    qdrant-client==1.7.0 \
    requests==2.31.0

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
