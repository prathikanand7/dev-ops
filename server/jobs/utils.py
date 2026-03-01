import json
import re
from kubernetes import client, config
from kubernetes.config.config_exception import ConfigException
from django.conf import settings

# TODO: The regex pattern only matches simple R assignment.
# Should be expanded to cover more complex assignments
# TODO: Refactor exception handling to be descriptive

def parse_notebook_parameters(notebook_file):
    """
    Retrieve parameters from the first cell of a given notebook
    """
    try:
        notebook_file.seek(0)
        content = json.load(notebook_file)
        
        first_cell = next((c for c in content['cells'] if c['cell_type'] == 'code'), None)
        if not first_cell:
            return []

        parameters = []
        
        r_parameter_name_pattern = re.compile(r'^(param_\w+)\s*<-\s*(.*)$')

        for line in first_cell['source']:
            line = line.strip()
            match = r_parameter_name_pattern.match(line)
            if match:
                name = match.group(1)
                value = match.group(2).strip('"\'')
                
                param_type = "string"
                # TODO: This fails for scientific notation
                if value.lower() in ['true', 'false', 't', 'f']:
                    param_type = "boolean"
                elif value.replace('.', '', 1).isdigit():
                    param_type = "number"

                parameters.append({
                    "name": name,
                    "default": value,
                    "type": param_type
                })
        return parameters

    except Exception as e:
        print(f"Error parsing notebook: {e}")
        return []
    
def parse_notebook_parameters_from_payload(param_list, request_data_items, request_files=None):
    final_payload = {}
    for param in param_list:
        var_name = param.get('name')
        if not var_name:
            continue
        
        val = param.get('default', '')
        if isinstance(val, str) and len(val) >= 2 and val.startswith(('"', "'")) and val.endswith(('"', "'")):
            val = val[1:-1]
        
        if val in [None, 'null']:
            val = ''
            
        final_payload[var_name] = val
    
    for key, value in request_data_items:
        if key not in (request_files or []): 
            final_payload[key] = value

    for key, val in final_payload.items():
        if isinstance(val, str):
            v_clean = val.strip()
            
            if v_clean.lower() == 'true':
                final_payload[key] = True
            elif v_clean.lower() == 'false':
                final_payload[key] = False
            elif v_clean.isdigit() or (v_clean.startswith('-') and v_clean[1:].isdigit()):
                final_payload[key] = int(v_clean)
            else:
                try:
                    final_payload[key] = float(v_clean)
                except ValueError:
                    final_payload[key] = val
    return final_payload


def get_absolute_url(base_url, file_url):
    if file_url.startswith('http'):
        return file_url
    base = base_url.rstrip('/')
    path = file_url.lstrip('/')
    return f"{base}/{path}"

def get_k8s_batch_client():
    """Handles Kubernetes authentication based on the environment."""

    if settings.ENVIRONMENT == "local":
        configuration = client.Configuration()
        configuration.host = settings.LOCAL_KUBECTL_PROXY_URL
        api_client = client.ApiClient(configuration)
        return client.BatchV1Api(api_client)
    
    try:
        config.load_incluster_config()
    except ConfigException:
        config.load_kube_config()
    return client.BatchV1Api()

def build_worker_payload(job_record, base_url):
    """Constructs the payload required by papermill."""
    notebook_url = get_absolute_url(base_url, job_record.notebook.notebook_file.url)
    
    payload = {
        "_notebook_url": notebook_url,
        "_notebook_filename": job_record.notebook.notebook_file.name.split('/')[-1],
        "_job_id": str(job_record.id),      
        "_base_url": base_url,        
        **job_record.job_parameters
    }
    
    if job_record.notebook.environment_file:
        payload["_environment_url"] = get_absolute_url(base_url, job_record.notebook.environment_file.url)
        
    if settings.ENVIRONMENT == "local":
        for key, val in payload.items():
            if isinstance(val, str) and "localhost:9000" in val:
                unsigned_url = val.split('?')[0]
                payload[key] = unsigned_url.replace("localhost:9000", "host.minikube.internal:9000")
                
    return payload

def build_k8s_job_spec(job_id, payload):
    """Constructs the Kubernetes Job manifest."""
    is_prod = (settings.ENVIRONMENT == "production")
    k8s_job_name = f"job-{str(job_id)[:8]}"
    
    # Ternary operators clean up the resource allocation logic
    resources = client.V1ResourceRequirements(
        requests={"cpu": "1" if is_prod else "250m", "memory": "2Gi" if is_prod else "512Mi"}, 
        limits={"cpu": "4" if is_prod else "2", "memory": "16Gi" if is_prod else "4Gi"}   
    )
    
    container = client.V1Container(
        name="notebook-worker",
        image=settings.WORKER_IMAGE,
        image_pull_policy="Always" if is_prod else "IfNotPresent", 
        command=["python"],
        args=["worker.py"], 
        working_dir="/app",
        resources=resources, 
        env=[
            client.V1EnvVar(name="JOB_PARAMETERS", value=json.dumps(payload)),
            client.V1EnvVar(name="WORKER_TOKEN", value=settings.WORKER_WEBHOOK_SECRET)
        ],
    )

    pod_spec_kwargs = {
        "containers": [container],
        "restart_policy": "Never",
        "service_account_name": "notebook-worker-sa"
    }

    # Apply Karpenter config only for prod
    if is_prod:
        pod_spec_kwargs["node_selector"] = {"workload-type": "light-notebook"}
        pod_spec_kwargs["tolerations"] = [
            client.V1Toleration(
                key="workload-type", operator="Equal", value="light-notebook", effect="NoSchedule"
            )
        ]

    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={"app": "notebook-runner"}),
        spec=client.V1PodSpec(**pod_spec_kwargs)
    )

    return client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(name=k8s_job_name),
        spec=client.V1JobSpec(template=template, backoff_limit=0, ttl_seconds_after_finished=3600)
    )