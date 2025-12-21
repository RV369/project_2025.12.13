# Dockerfile
FROM python:3.11

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 
RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*
COPY . .
CMD ["python", "-m", "bot.main"]
