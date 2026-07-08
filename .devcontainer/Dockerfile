FROM mcr.microsoft.com/devcontainers/python:3.12
RUN apt-get update \
    && apt-get install -y --no-install-recommends poppler-utils \
    && rm -rf /var/lib/apt/lists/*
