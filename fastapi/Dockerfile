# syntax=docker/dockerfile:1.3
FROM python:3.9-slim-buster

WORKDIR /app

# 
# WORKDIR /code
COPY requirements.txt .

# 
# ARG FTP_SERVER
# COPY use-secret.sh .
# RUN --mount=type=secret,id=ftp_server ./use-secret.sh
# RUN --mount=type=secret,id=ftp_server ./use_secret.sh


RUN apt-get update && apt-get install -y \
    gcc \
    git \
    tk \
    musl-dev \
    linux-headers-amd64 \
    postgresql \
    python3-dev \
    proj-bin \
    libgeos-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
# COPY ../appdata ../appdata
# COPY .git /code/.git
# VOLUME /appdata
# 

# OLD UVICORN COMMAND 11/17/2022
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
CMD ["gunicorn", "app.main:app", "--workers", "2","--worker-class","uvicorn.workers.UvicornWorker","--bind","0.0.0.0:80","--timeout","5000","--keep-alive","2000"]

EXPOSE 80