from django.urls import path
from . import views
from .views import TriggerJobAPI

urlpatterns = [
    # UI Paths
    path('upload/', views.upload_notebook, name='upload_notebook'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Token management paths
    path('token/status/', views.check_token_status, name='token_status'),
    path('token/generate/', views.generate_new_token, name='generate_token'),
    
    # API Paths
    path('api/delete-notebook/<uuid:notebook_id>/', views.delete_notebook, name='delete_notebook'),
    path('api/delete-job/<uuid:job_id>/', views.delete_job, name='delete_job'),
    path('api/run/', TriggerJobAPI.as_view(), name='trigger_job'),
    path('api/jobs/<uuid:job_id>/complete/', views.job_complete_callback, name='job_complete_callback'),
    path('api/jobs/poll-status/', views.poll_job_statuses, name='poll_job_statuses'),
    path('api/jobs/<uuid:job_id>/logs/', views.get_job_logs, name='get_job_logs'),
    path('api/notebooks/<uuid:notebook_id>/run/', views.TriggerNotebookAPIView.as_view(), name='api_trigger_notebook'),
    path('api/jobs/<uuid:job_id>/status/', views.JobStatusAPIView.as_view(), name='api_job_status'),
]