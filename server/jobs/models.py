from django.db import models
from django.contrib.auth.models import User
import uuid

class Notebook(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    notebook_file = models.FileField(upload_to='notebooks/')
    environment_file = models.FileField(upload_to='environments/', help_text="The environment.yaml or renv.lock file")
    
    parameter_schema = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name

class InputFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to='inputs/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.file.name} ({self.owner.username})"

class Job(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROVISIONING', 'Provisioning Resources'),
        ('RUNNING', 'Running'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
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
    
    logs = models.TextField(blank=True)
    result_file = models.FileField(upload_to='results/', null=True, blank=True)

    def __str__(self):
        return f"{self.notebook.name} - {self.status}"