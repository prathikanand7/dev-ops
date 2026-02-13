# Quick Start Commands

## Create Virtual Environment
Assuming you have python, pip and venv installed...
```
python -m venv .env
./.env/scripts/activate
pip install -r requirments.txt
```

## Start Kubernetes
```
minikube start --driver=docker
```

## Start Redis
```
docker run -d -p 6379:6379 redis
```

## Start Server
Bust be in server directory
```
cd .\.env\Scripts\Activate
python manage.py runserver
```

## Start Celery
## Must be in server directory
```
.\.env\Scripts\Activate
celery -A notebook_platform worker --loglevel=info --pool=solo
```

## Watch the pods (Optional)
```
kubectl get pods --watch
```

Get the logs for a specific pod:
```
kubectl logs -f <NAME>
```

## Build the Container
Get in Miniqube first (Miniqube must be running)
```
& minikube -p minikube docker-env --shell powershell | Invoke-Expression
```
Then go to the worker directory and build

```
docker build -t r-notebook-worker .
```