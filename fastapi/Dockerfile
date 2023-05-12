# syntax=docker/dockerfile:1.3
FROM python:3

# 
# WORKDIR /code

# 
COPY ./requirements.txt requirements.txt
# ARG FTP_SERVER
# COPY use-secret.sh .
# RUN --mount=type=secret,id=ftp_server ./use-secret.sh
# RUN --mount=type=secret,id=ftp_server ./use_secret.sh
RUN pip install --no-cache-dir --upgrade -r requirements.txt
# 

COPY ./app /app
# COPY ../appdata ../appdata
# COPY .git /code/.git
# VOLUME /appdata
# 

# OLD UVICORN COMMAND 11/17/2022
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
CMD ["gunicorn", "app.main:app", "--workers", "2","--worker-class","uvicorn.workers.UvicornWorker","--bind","0.0.0.0:80","--timeout","0","--keep-alive","2000"]

EXPOSE 80