FROM python:3.12-slim

# Instalar dependencias del sistema necesarias para ffmpeg, whisper y playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    fonts-liberation \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install-deps chromium && playwright install chromium

# Copiar el código del proyecto
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
