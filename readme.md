# Quick Start Commands

# Start Kubernetes
minikube start --driver=docker

# Start Redis
docker run -d -p 6379:6379 redis

# Start Server
.\.env\Scripts\Activate
python manage.py runserver

# Start Celery
.\.env\Scripts\Activate
celery -A notebook_platform worker --loglevel=info --pool=solo

# Watch the pods
kubectl get pods --watch

# Build the Container
## Get in Miniqube first (Miniqube must be running)
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

## Then build
docker build -t r-notebook-worker .

# Run Docker Container Manually
$Params = '{"_notebook_filename": "Data_cleaning.ipynb", "param_01_input_data_filename": "Template_MBO_Example_raw_v3.xlsx", "param_09_years": 7}'

docker run --rm `
>>   -v ${PWD}:/app `
>>   -e JOB_PARAMETERS=$Params `
>>   r-notebook-worker python worker.py
