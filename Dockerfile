# Dockerfile
FROM registry.access.redhat.com/ubi9-minimal:9.3-1612

# Create a non-root user
RUN microdnf install -y shadow-utils && \
    groupadd -r appuser && useradd -r -g appuser appuser && \
    microdnf clean all

WORKDIR /app

# Install Python and development dependencies
RUN microdnf install -y python3 python3-pip && \
    microdnf clean all

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY src ./src
ENV PYTHONUNBUFFERED=1

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

EXPOSE 8000
CMD ["python3", "-m", "uvicorn", "src.server.server:app", "--host", "0.0.0.0", "--port", "8000"]
