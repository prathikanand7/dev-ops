from rest_framework import serializers
from .models import Notebook, Job

class NotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ['id', 'name', 'description', 'created_at', 'notebook_file', 'environment_file', 'parameter_schema']
        read_only_fields = ['id', 'created_at', 'parameter_schema']

class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'notebook', 'status', 'created_at', 'finished_at', 'output_file', 'environment_file', 'job_parameters', 'logs', 'result_file']
        read_only_fields = ['id', 'status', 'created_at', 'finished_at', 'output_file', 'job_parameters', 'logs', 'result_file']