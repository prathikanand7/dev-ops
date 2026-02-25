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
    environment_file = models.FileField(upload_to='environments/',null=True, blank=True, help_text="The environment.yaml or renv.lock file")
    
    parameter_schema = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name
