import os
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from rest_framework.authtoken.models import Token
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from notebook_platform.settings import WORKER_CALLBACK_URL

from .forms import NotebookUploadForm
from .models import Job, Notebook
from .tasks import dispatch_job_task
from .utils import parse_notebook_parameters, parse_notebook_parameters_from_payload

BASE_URL = WORKER_CALLBACK_URL.rstrip('/')

def get_safe_url(raw_url):
    if raw_url.startswith('http'):
        return raw_url
    if not raw_url.startswith('/'):
        raw_url = '/' + raw_url
    return f"{BASE_URL}{raw_url}"

@login_required
def check_token_status(request):
    has_token = Token.objects.filter(user=request.user).exists()
    return JsonResponse({'has_token': has_token})

@login_required
@require_POST
def generate_new_token(request):
    Token.objects.filter(user=request.user).delete()
    new_token = Token.objects.create(user=request.user)
    return JsonResponse({'token': new_token.key})

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
            notebook = Notebook.objects.get(id=notebook_id, owner=request.user)
        except Notebook.DoesNotExist:
            return Response({"error": "Notebook not found or you do not have permission to access it."}, status=404)

        params = {}

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
            saved_path = default_storage.save(f"inputs/{uploaded_file.name}", uploaded_file)
            
            raw_url = default_storage.url(saved_path)
            file_url = get_safe_url(raw_url)
            
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
        transaction.on_commit(lambda: dispatch_job_task.delay(job.id))

        return Response({
            "job_id": job.id, 
            "status": "PENDING",
            "message": "Job queued successfully."
        }, status=201)
    

# TODO: This must be protected somehow. Have to think of the best way to do it
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
    jobs = Job.objects.filter(user=request.user).order_by('-created_at')[:50]
    
    job_data = []
    for job in jobs:
        file_url = None
        if job.output_file:
            try:
                file_url = job.output_file.url
            except Exception:
                pass
            
        job_data.append({
            'id': str(job.id),
            'status': job.status,
            'file_url': file_url
        })
        
    return JsonResponse({'jobs': job_data})


@login_required
def get_job_logs(request, job_id):
    """Returns the text logs for a specific job."""
    job = get_object_or_404(Job, id=job_id, user=request.user)
    return JsonResponse({'logs': job.logs or "No logs available yet..."})


class TriggerNotebookAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, notebook_id):
        try:
            notebook = Notebook.objects.get(id=notebook_id, owner=request.user)
            
            final_payload = {}
            schema_data = notebook.parameter_schema
            param_list = [item for item in schema_data if isinstance(item, dict)]

            final_payload = parse_notebook_parameters_from_payload(param_list, request.data.items(), request.FILES)

            for key, uploaded_file in request.FILES.items():
                saved_path = default_storage.save(f"api_uploads/{uploaded_file.name}", uploaded_file)
                
                raw_url = default_storage.url(saved_path)
                file_url = get_safe_url(raw_url)
                
                final_payload[f"_download_{key}"] = file_url
                final_payload[key] = os.path.basename(saved_path)
            
            job = Job.objects.create(
                user=request.user,
                notebook=notebook,
                status='PENDING',
                job_parameters=final_payload
            )

            transaction.on_commit(lambda: dispatch_job_task.delay(job.id))

            return Response({
                "message": "Job successfully queued.",
                "job_id": str(job.id),
                "status": "PENDING",
                "resolved_payload": final_payload 
            }, status=status.HTTP_202_ACCEPTED)

        except Notebook.DoesNotExist:
            return Response(
                {"error": "Notebook not found or you do not have permission to access it."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"Server Error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
class JobStatusAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id, user=request.user)
        
        response_data = {
            "job_id": str(job.id),
            "status": job.status,
            "logs": job.logs if job.logs else "No logs available yet."
        }

        if job.status == 'SUCCESS' and job.output_file:
            try:
                raw_url = job.output_file.url
                if raw_url.startswith('http'):
                    response_data['download_url'] = raw_url
                else:
                    response_data['download_url'] = request.build_absolute_uri(raw_url)
            except Exception:
                pass
        
        elif job.status == 'FAILED':
            response_data['error_message'] = "Execution failed. Please review the logs."

        return Response(response_data, status=status.HTTP_200_OK)