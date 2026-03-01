# Notebook Platform - Local Setup Guide

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## Project Structure
```
dev-ops/
├── server/                     # Django web app + Celery worker config
│   ├── jobs/                   # Core app (models, views, tasks)
│   ├── notebook_platform/      # Django project settings
│   ├── k8s-manifests/          # Kubernetes manifests (optional, not sure if we will use these w/ Terraform)
│   ├── docker-compose.yml
│   ├── Dockerfile
│   └── requirements.txt
├── worker/                     # Notebook execution worker
│   ├── Dockerfile
│   ├── worker.py
│   └── inputs/
│       └── environment.yaml    # Base env for all runners, can be updated in runtime based on input files
└── .github/
    └── workflows/
        └── ci.yaml             # Define actions
```
## Quick Start

### 1. Build and Start All Services
You will need to do this every time you want to develop locally.
```
cd server
docker compose up --build -d 
```
This will spin up the following server components:
- PostgreSQL Database               # Stand-in for RDS, not used in production
- Redis Cache (Used by Celery)      # Stand-in for ElastiCache, not used in production
- Minio                             # Stand-in for S3, not used in production
- Celery Service
- Django Server

### 2. Run Database Migrations (First Time ONLY)
This is usually needed when running for the first time, or when making changes to the models.
In a separate terminal:
```
docker compose exec web python manage.py migrate
```
### 3. Create a Superuser (First Time ONLY)
```
docker compose exec web python manage.py createsuperuser
```
### 4. Start minikube
```
minikube start --driver=docker
```
### 5. Apply rbac.yaml (First Time ONLY)
```
cd server
kubectl apply -f minikube-rbac.yaml
```
### 6. Build Worker
This will build the image inside minikube.
```
minikube image build -t r-notebook-worker:latest .
```
### 7. Create Network Proxy (Windows Only)
```
kubectl proxy --address='0.0.0.0' --port=8001 --accept-hosts='^.*'
```

### 8. Access the Application
```
http://localhost:8000
```

## Useful Commands
```
# View Jobs (-w to keep in running)
kubectl get pods -w

# Get the logs of a specific job
kubectl logs <NAME>

# Run commands inside the web container
docker compose exec web python <SOME COMMAND>

# Open a shell inside the web container
docker compose exec web bash

# Run tests inside docker
docker compose exec web python manage.py test
```

## CI/CD
A GitHub Actions workflow is located at `.github/workflows/ci.yaml` and runs automatically on push or can be triggered manually.
It builds everything as described above, uses a cache to speed up things, and runs a GET to the login screen to verify things are running.

## AWS Deployment with Zappa

The Django server is deployed to AWS Lambda using Zappa. To keep secrets out of version control, we use a template for the Zappa configuration and inject environment variables during deployment.

### AWS Prerequisites
Before deploying, ensure the following resources and credentials exist in your AWS account:
- **IAM User:** Credentials configured locally or in the CI/CD pipeline with permissions to manage Lambda, API Gateway, S3, and IAM roles.
- **S3 Deployment Bucket:** A bucket for Zappa to store its zip packages during deployment. Different that the Django storage bucket.
- **RDS PostgreSQL Instance:** Production database (replacing the local Docker Postgres).
- **S3 Storage Bucket:** A bucket for Django's static and media files (replacing the local Minio setup).

### Environment
We use `zappa_settings.template.json` as our base. The secrets are provided and replaced through environment variables. If deploying locally, export these variables in the terminal or use an env file. In CI/CD, set these as pipeline secrets.

These must be set:
```
export AWS_REGION="eu-west-1"
export S3_ZAPPA_BUCKET_NAME="your-zappa-deploy-bucket"
export DJANGO_SECRET_KEY="your_secure_secret_key"
export DATABASE_URL="postgres://user:url_encoded_password@rds-host:5432/dbname"
export AWS_STORAGE_BUCKET_NAME="your-app-storage-bucket"
export ALLOWED_HOSTS="your-api-gateway-url.amazonaws.com"
export WORKER_CALLBACK_URL="https://your-api-gateway-url.amazonaws.com"
export WORKER_WEBHOOK_SECRET="your_secret"
```

### Build and Deploy
Generate the final configuration file and deploy:
```
# Generate the active settings file by replacing placeholders
envsubst < zappa_settings.template.json > zappa_settings.json

# Deploy for the first time
zappa deploy dev

# OR, update an existing deployment
zappa update dev
```