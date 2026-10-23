# Dockerfile for Resonance Club Web Platform
FROM python:3.11-slim

WORKDIR /app

# Copy website and audio assets
COPY . /app/

# Expose web port
EXPOSE 3000

# Run the Range-enabled Python server
CMD ["python3", "serve.py", "3000"]
