from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from .models import Notebook, Job
from .forms import NotebookUploadForm 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .tasks import dispatch_job_task
from .utils import parse_notebook_parameters
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Job
import os

BASE_URL = "http://host.docker.internal:8000"

@login_required
def upload_notebook(request):
    if request.method == 'POST':
        form = NotebookUploadForm(request.POST, request.FILES)
        if form.is_valid():
            nb = form.save(commit=False)
            nb.owner = request.user
            
            extracted_params = parse_notebook_parameters(request.FILES['notebook_file'])
            nb.parameter_schema = extracted_params
            
            nb.save()
            return redirect('dashboard')
    else:
        form = NotebookUploadForm()
    return render(request, 'upload.html', {'form': form})

@login_required
def dashboard(request):
    notebooks = Notebook.objects.filter(owner=request.user).order_by('-created_at')
    jobs = Job.objects.filter(user=request.user).order_by('-created_at')
    
    return render(request, 'dashboard.html', {'notebooks': notebooks, 'jobs': jobs})

@login_required
@require_POST
def delete_notebook(request, notebook_id):
    notebook = get_object_or_404(Notebook, id=notebook_id, owner=request.user)
    notebook.delete()
    return JsonResponse({"status": "success", "message": "Notebook deleted."})

@login_required
@require_POST
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, user=request.user)
    job.delete()
    return JsonResponse({"status": "success", "message": "Job deleted."})

class TriggerJobAPI(APIView):
    """
    POST /api/run/
    Payload: multipart/form-data (Files and Text fields)
    """
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notebook_id = request.data.get('notebook_id')
        if not notebook_id:
            return Response({"error": "notebook_id is required."}, status=400)
            
        try:
            notebook = Notebook.objects.get(id=notebook_id)
        except Notebook.DoesNotExist:
            return Response({"error": "Notebook not found"}, status=404)

        params = {}
        base_url = BASE_URL

        for key, value in request.POST.items():
            if key not in ['notebook_id', 'csrfmiddlewaretoken']:
                if str(value).isdigit():
                    params[key] = int(value)
                else:
                    try:
                        params[key] = float(value)
                    except ValueError:
                        params[key] = value

        for key, uploaded_file in request.FILES.items():
            
            # Save the file securely to media/inputs/
            saved_path = default_storage.save(f"inputs/{uploaded_file.name}", uploaded_file)
            file_url = f"{base_url}{default_storage.url(saved_path)}"
            
            local_filename = os.path.basename(saved_path)
            params[key] = local_filename
            params[f"_download_{key}"] = file_url

        # Create the Job Record
        job = Job.objects.create(
            notebook=notebook,
            user=request.user,
            job_parameters=params,
            status='PENDING'
        )

        # Send to Celery
        dispatch_job_task.delay(job_id=str(job.id))

        return Response({
            "job_id": job.id, 
            "status": "PENDING",
            "message": "Job queued successfully."
        }, status=201)
    
    
@csrf_exempt
@require_POST
def job_complete_callback(request, job_id):
    """
    Webhook for the Kubernetes worker 
    """
    job = get_object_or_404(Job, id=job_id)
    
    status = request.POST.get('status', 'SUCCESS')
    logs = request.POST.get('logs', '')
    
    job.status = status
    job.logs = logs
    
    # Save file if provided
    if 'output_file' in request.FILES:
        job.output_file = request.FILES['output_file']
        
    job.save()
    return JsonResponse({"message": f"Job {job_id} updated successfully."})


@login_required
def poll_job_statuses(request):
    """Returns the live status of all jobs for the current user."""
    jobs = Job.objects.filter(user=request.user).values('id', 'status', 'output_file')
    
    job_data = []
    for job in jobs:
        file_url = None
        if job['output_file']:
            from django.conf import settings
            file_url = f"{settings.MEDIA_URL}{job['output_file']}"
            
        job_data.append({
            'id': str(job['id']),
            'status': job['status'],
            'file_url': file_url
        })
        
    return JsonResponse({'jobs': job_data})

@login_required
def get_job_logs(request, job_id):
    """Returns the text logs for a specific job."""
    job = get_object_or_404(Job, id=job_id, user=request.user)
    return JsonResponse({'logs': job.logs or "No logs available yet..."})