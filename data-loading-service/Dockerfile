# syntax=docker/dockerfile:1.3
FROM lacmta/geodb-base
# 2161.3s
# 
# WORKDIR /code
WORKDIR /app

# 
COPY requirements.txt .
# ARG FTP_SERVER
# COPY use-secret.sh .
# RUN --mount=type=secret,id=ftp_server ./use-secret.sh
# RUN --mount=type=secret,id=ftp_server ./use_secret.sh
# RUN pip install --upgrade cython

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
# COPY ../appdata /appdata
# COPY .git /code/.git
# 
CMD ["python","app/main.py"]
