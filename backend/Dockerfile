FROM python:3.11-slim

# Prevent Python from writing .pyc files
# and keep logs visible in Docker.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required by Rasterio/GDAL.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory.
WORKDIR /app

# Copy dependency file first for Docker layer caching.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code.
COPY app ./app

# Create runtime directories.
RUN mkdir -p data/uploads data/reports

# Expose FastAPI port.
EXPOSE 8000

# Start SatQuery backend.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]