FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# fonts-dejavu-core 给验证码图片提供可用字体
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==22.0.0

COPY app.py index.html index_maintenance.html IMG_8105.JPG ./
COPY templates/ templates/
COPY static/ static/

RUN mkdir -p static/captcha

EXPOSE 5000

CMD ["gunicorn", \
     "--workers", "3", \
     "--bind", "0.0.0.0:5000", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--forwarded-allow-ips", "*", \
     "app:app"]
