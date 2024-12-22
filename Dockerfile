FROM python:3.12-slim

ENV PYTHONUNBUFFERED=TRUE
COPY requirements.txt /src/requirements.txt

RUN pip3 install -r /src/requirements.txt && \
  mkdir -p /download && \
  mkdir -p /metadata

ADD main.py /src
ADD backups3 /src/backups3

WORKDIR /src

EXPOSE 8000

ENTRYPOINT ["python3", "main.py"]
