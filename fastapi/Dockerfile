# syntax=docker/dockerfile:1.3
FROM lacmta/geodb-base

WORKDIR /app

COPY requirements.txt .

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
    pgbouncer \
    gosu \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a new user and switch to that user
RUN useradd -ms /bin/bash pgbouncer && \
    chown -R pgbouncer:pgbouncer /etc/pgbouncer

CMD python -c "\
import os;\
from urllib.parse import urlparse;\
result = urlparse(os.environ['API_DB_URI']);\
print(f'export DB_USER={result.username}');\
print(f'export DB_PASSWORD={result.password}');\
print(f'export DB_HOST={result.hostname}');\
print(f'export DB_PORT={result.port}');\
print(f'export DB_NAME={result.path[1:]}')" > /tmp/env.sh && \
    . /tmp/env.sh && \
    echo "\"$DB_USER\" \"md5`echo -n \"$DB_PASSWORD$DB_USER\" | md5sum | cut -d ' ' -f1`\"" > /etc/pgbouncer/userlist.txt && \
    echo "[databases]" > /etc/pgbouncer/pgbouncer.ini && \
    echo "$DB_NAME = host=$DB_HOST port=$DB_PORT dbname=$DB_NAME user=$DB_USER password='$DB_PASSWORD'" >> /etc/pgbouncer/pgbouncer.ini && \
    echo "[pgbouncer]" >> /etc/pgbouncer/pgbouncer.ini && \
    echo "listen_port = 6432" >> /etc/pgbouncer/pgbouncer.ini && \
    echo "listen_addr = *" >> /etc/pgbouncer/pgbouncer.ini && \
    echo "auth_type = md5" >> /etc/pgbouncer/pgbouncer.ini && \
    echo "auth_file = /etc/pgbouncer/userlist.txt" >> /etc/pgbouncer/pgbouncer.ini && \
    echo "client_login_timeout = 120" >> /etc/pgbouncer/pgbouncer.ini && \
    gosu pgbouncer pgbouncer /etc/pgbouncer/pgbouncer.ini & \
    gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80 --timeout 120 --keep-alive 5

EXPOSE 80