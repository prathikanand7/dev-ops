# Notebook Platform — Local Setup Guide

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
        └── ci.yaml #
```

## Quick Start

### 1. Build and Start All Services
You will need to do this every time you want to develop locally.

```bash
cd server
docker compose up --build -d 
```
This will spin up the following server components
    - PostgreSQL Database               # Stand-in for RDS, not used in production
    - Redis Cache (Used by Celery)      # Stand-in for ElastiCache, not used in production
    - Minio                             # Stand-in for S3, not used in production
    - Celery Service
    - Django Server

### 2. Run Database Migrations (First Time ONLY)
This is usually needed when running for the first time, or when making changes to the models
In a separate terminal:
```bash
docker compose exec web python manage.py migrate
```

### 3. Create a Superuser (First Time ONLY)
```bash
docker compose exec web python manage.py createsuperuser
```

### 4. Start minikube
```bash
minikube start --driver=docker
```

### 5. Apply rbac.yaml (First Time ONLY)
```bash
cd server
kubectl apply -f minikube-rbac.yaml
```

### 6. Build Worker
This will build the image inside minikube
```bash
minikube image build -t r-notebook-worker:latest .
```

### 7. Create Network Proxy (Windows Only)
```
kubectl proxy --address='0.0.0.0' --port=8001 --accept-hosts='^.*'
```

### 8. Access the Application

| Service         | URL                          |
| --------------- | ---------------------------- |
| Web Application | <http://localhost:8000>      |

## Useful Commands

```bash
# View Jobs (-w to keep in running)
kubectl get pods -w

# Get the logs of a specific job
kubectl logs <NAME>

# Run commands inside the web container
docker compose exec web python <SOME COMMAND>

# Open a shell inside the web container
docker compose exec web bash
```

## CI/CD
A GitHub Actions workflow is located at `.github/workflows/ci.yaml` and runs automatically on push or can be triggered manually.
It builds everything as described above, uses a cache to speed up things, and runs a GET to the login screen to verify things are running.