FROM python:3.11-slim-bookworm AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN sed -i 's|http://deb.debian.org|https://deb.debian.org|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

FROM base AS dev
COPY requirements.txt requirements.txt
COPY requirements-dev.txt requirements-dev.txt
RUN pip install --upgrade pip \
    && pip install -r requirements-dev.txt
COPY . .
ENV PYTHONPATH=/app/src
CMD ["uvicorn", "idcard_ocr.api.app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

FROM base AS runtime
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip \
    && pip install -r requirements.txt
COPY . .
ENV PYTHONPATH=/app/src
EXPOSE 8080
CMD ["uvicorn", "idcard_ocr.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
