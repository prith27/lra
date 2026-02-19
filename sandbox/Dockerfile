FROM python:3.12-slim

# Run as non-root
RUN useradd -m sandbox
USER sandbox

WORKDIR /app

# Minimal deps for kernel server
COPY --chown=sandbox:sandbox kernel_server.py .
RUN pip install --user --no-cache-dir fastapi uvicorn pydantic

# Disable Python output buffering
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "kernel_server:app", "--host", "0.0.0.0", "--port", "8000"]
