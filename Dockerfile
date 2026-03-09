FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/
RUN pip install --no-cache-dir .

EXPOSE 8965

CMD ["python", "-m", "mikrotik_management_mcp", "--transport", "http", "--port", "8965"]
