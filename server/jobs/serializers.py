from rest_framework import serializers
from .models import Notebook, Job, InputFile

class NotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ['id', 'name', 'description', 'created_at', 'parameter_schema']
        read_only_fields = ['parameter_schema', 'owner']

class JobCreateSerializer(serializers.Serializer):
    notebook_id = serializers.UUIDField()
    parameters = serializers.JSONField(required=False, default=dict)

class JobStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'status', 'created_at', 'finished_at', 'result_file']