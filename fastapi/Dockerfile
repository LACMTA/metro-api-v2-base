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
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt

# Copy the pgbouncer configuration file
COPY pgbouncer.ini /etc/pgbouncer/pgbouncer.ini

COPY . .

CMD export DB_USER=$(echo $API_DB_URI | cut -d'/' -f3 | cut -d':' -f1) && \
    export DB_PASSWORD=$(echo $API_DB_URI | cut -d'/' -f3 | cut -d':' -f2 | cut -d'@' -f1) && \
    echo "$DB_USER:md5`echo -n "$DB_PASSWORD$DB_USER" | md5sum | cut -d ' ' -f1`" > /etc/pgbouncer/userlist.txt && \
    gunicorn app.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:80 --timeout 120 --keep-alive 5

EXPOSE 80