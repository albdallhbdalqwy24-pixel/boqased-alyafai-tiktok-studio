FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY videofx_studio.py /app/videofx_studio.py

ENV PYTHONUNBUFFERED=1
EXPOSE 10000

CMD ["python3", "/app/videofx_studio.py"]
