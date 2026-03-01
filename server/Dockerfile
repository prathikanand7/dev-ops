FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python Packages
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY . /app/

# Gather static files for whitenoise
# Use dummy values to build the image, these will not persist in the image
ARG DJANGO_SECRET_KEY=dummy-build-key
ARG WORKER_CALLBACK_URL=http://dummy-build-url
ARG CELERY_BROKER_URL=redis://dummy-build-url
ARG WORKER_WEBHOOK_SECRET=dummy-build-secret
ARG WORKER_IMAGE=dummy-worker-image

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "notebook_platform.wsgi:application"]