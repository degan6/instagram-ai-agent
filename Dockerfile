FROM python:3.12-slim-bookworm
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg fonts-dejavu-core fonts-liberation tini && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/ig-agent
COPY pyproject.toml README.md LICENSE MANIFEST.in ./
COPY src ./src
RUN pip install . && playwright install --with-deps chromium && rm -rf /var/lib/apt/lists/*
COPY data /opt/seed-data
COPY docker /opt/docker
RUN python /opt/docker/test_entrypoint.py
RUN useradd --uid 10001 --create-home agent && mkdir /workspace && chown agent:agent /workspace
WORKDIR /workspace
USER agent
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 CMD ["python", "/opt/docker/healthcheck.py"]
ENTRYPOINT ["/usr/bin/tini", "--", "python", "/opt/docker/entrypoint.py"]
CMD ["dashboard", "--host", "0.0.0.0", "--port", "8080"]
