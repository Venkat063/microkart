# One Dockerfile for every service: docker build -f docker/Dockerfile --build-arg SERVICE=cart .
FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/app/common
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY common ./common
ARG SERVICE
COPY services/${SERVICE} ./service
# Numeric UID so Kubernetes can enforce runAsNonRoot.
RUN useradd -r -u 10001 app && chown -R 10001 /app
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://127.0.0.1:8000/health')"
CMD ["uvicorn", "--app-dir", "/app/service", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
