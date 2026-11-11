FROM python:3.12-slim

# GDAL/GEOS for GeoDjango (PostGIS on Neon)
RUN apt-get update \
 && apt-get install -y --no-install-recommends gdal-bin libgdal-dev libgeos-dev \
 && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN SECRET_KEY=build DEBUG=False USE_SQLITE=True python manage.py collectstatic --noinput

# Render sets $PORT. Migrate on boot, then serve HTTP + WebSocket via Daphne.
CMD python manage.py migrate --noinput && daphne -b 0.0.0.0 -p ${PORT:-8000} config.asgi:application
