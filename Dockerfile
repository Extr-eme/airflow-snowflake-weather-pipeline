FROM apache/airflow:2.9.3

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    openmeteo_requests \
    requests-cache \
    retry-requests \
    pandas
