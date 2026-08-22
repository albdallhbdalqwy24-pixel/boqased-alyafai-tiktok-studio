FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "mediapipe==0.10.21" numpy pillow

WORKDIR /app
COPY videofx_studio.py /app/videofx_studio.py
COPY ai_silhouette.py /app/ai_silhouette.py
COPY web /app/web

ENV PYTHONUNBUFFERED=1
EXPOSE 10000

CMD ["python3", "/app/videofx_studio.py"]
