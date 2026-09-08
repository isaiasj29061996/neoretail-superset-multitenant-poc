FROM python:3.11-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

WORKDIR /workspace
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      ca-certificates curl git openjdk-17-jre-headless libpostgresql-jdbc-java \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY . /workspace/local-engine
EXPOSE 8888
CMD ["sh", "/workspace/local-engine/entrypoint.sh"]
