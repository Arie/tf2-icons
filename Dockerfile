# TF2 Killicons Sprite Generator
# Docker image for generating TF2 killicon sprite sheets

FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml ./
COPY generate.py ./
COPY generate_preview.py ./

# Create required directories
RUN mkdir -p vpk dist community

# Install dependencies
RUN pip install --no-cache-dir vpk>=1.4.0 srctools>=2.3.0 Pillow>=10.0.0

# Set volumes for user-provided data
VOLUME ["/app/vpk", "/app/community", "/app/dist"]

# Run the generator by default
CMD ["python3", "generate.py"]
