FROM python:3.11-slim

WORKDIR /app

# Install build tools and Pillow dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency requirements and source code
COPY . /app/

# Install python dependencies
RUN pip install --no-cache-dir \
    numpy \
    pillow \
    ecdsa \
    fastapi \
    uvicorn \
    pydantic \
    python-multipart

# Make scripts executable
RUN chmod +x /app/stegstr-cli && chmod +x /app/scripts/*.sh

EXPOSE 8765

CMD ["python3", "-m", "stegstr.api.server"]
