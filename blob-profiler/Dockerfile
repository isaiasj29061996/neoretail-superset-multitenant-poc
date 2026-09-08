FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
COPY profile_blob.py /app/profile_blob.py
ENTRYPOINT ["python", "/app/profile_blob.py"]
