from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from jobs.models import Job

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Successful Job Example',
            summary='A completed job status response',
            value={
                "id": "f5815610-8b77-4cfb-81d3-659f4258d4bf",
                "notebook": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "status": "SUCCESS",
                "created_at": "2024-10-25T14:20:00Z",
                "finished_at": "2024-10-25T14:25:00Z",
                "output_file": "http://localhost:8000/media/job_outputs/results.zip",
                "environment_file": None,
                "job_parameters": {
                    "dataset": "uploaded_data_123.csv",
                    "iterations": 500
                },
                "logs": "Execution started...\nLoading libraries...\nCompleted successfully.",
                "result_file": None
            }
        )
    ]
)
class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'notebook', 'status', 'created_at', 'finished_at', 'output_file', 'environment_file', 'job_parameters', 'logs', 'result_file']
        read_only_fields = ['id', 'status', 'created_at', 'finished_at', 'output_file', 'job_parameters', 'logs', 'result_file']
        extra_kwargs = {
            'job_parameters': {
                'help_text': 'The exact dictionary of parameters that were passed to the Kubernetes worker for this specific run.'
            },
            'logs': {
                'help_text': 'Raw stdout/stderr text output from the execution container.'
            }
        }