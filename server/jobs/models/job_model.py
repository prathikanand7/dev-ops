from django.db import models
from django.contrib.auth.models import User
import uuid
from .notebook_model import Notebook

class Job(models.Model):
    STATUS_CHOICES = [
        # Legacy statuses (for backward compatibility)
        ('PENDING', 'Pending'),
        ('PROVISIONING', 'Provisioning Resources'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
        # AWS Batch statuses
        ('SUBMITTED', 'Submitted'),
        ('RUNNABLE', 'Runnable'),
        ('STARTING', 'Starting'),
        ('SUCCEEDED', 'Succeeded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    output_file = models.FileField(upload_to='job_outputs/', null=True, blank=True)
    environment_file = models.FileField(upload_to='environments/', null=True, blank=True, help_text="Optional: environment.yaml for extra dependencies")
    
    job_parameters = models.JSONField(default=dict)
    
    # AWS Batch specific fields
    aws_batch_job_id = models.CharField(max_length=255, null=True, blank=True, help_text="AWS Batch Job ID")
    aws_batch_job_queue = models.CharField(max_length=255, null=True, blank=True, help_text="AWS Batch Job Queue")
    aws_batch_job_definition = models.CharField(max_length=255, null=True, blank=True, help_text="AWS Batch Job Definition")
    
    logs = models.TextField(blank=True)
    result_file = models.FileField(upload_to='results/', null=True, blank=True)

    def __str__(self):
        return f"{self.notebook.name} - {self.status}"