FROM python:3.11-slim

# Install acli binary
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LO "https://acli.atlassian.com/linux/latest/acli_linux_amd64/acli" \
    && chmod +x acli \
    && mv acli /usr/local/bin/

# Install pyacli
WORKDIR /app
COPY pyproject.toml poetry.lock README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

ENTRYPOINT ["python"]
