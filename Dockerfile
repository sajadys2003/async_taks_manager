FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN echo 'Acquire::http::Proxy "http://127.0.0.1:10990";' > /etc/apt/apt.conf.d/proxy.conf && \
    echo 'Acquire::https::Proxy "http://127.0.0.1:10990";' >> /etc/apt/apt.conf.d/proxy.conf


RUN echo 'Acquire::ForceIPv4 "true";' > /etc/apt/apt.conf.d/99force-ipv4

ARG HTTP_PROXY="http://127.0.0.1:10990"
ARG HTTPS_PROXY="http://127.0.0.1:10990"
ARG http_proxy="http://127.0.0.1:10990"
ARG https_proxy="http://127.0.0.1:10990"

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .


RUN pip install --proxy="http://127.0.0.1:10990" --no-cache-dir -r requirements.txt

COPY . .
ENV PYTHONPATH=/app
