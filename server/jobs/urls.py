from django.urls import path
from . import views
from .views import TriggerJobAPI

urlpatterns = [
    # UI Paths
    path('upload/', views.upload_notebook, name='upload_notebook'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    
    # API Paths
    path('api/delete-notebook/<str:notebook_id>/', views.delete_notebook, name='delete_notebook'),
    path('api/delete-job/<str:job_id>/', views.delete_job, name='delete_job'),
    path('api/run/', TriggerJobAPI.as_view(), name='trigger_job'),
    path('api/jobs/<str:job_id>/complete/', views.job_complete_callback, name='job_complete_callback'),
]