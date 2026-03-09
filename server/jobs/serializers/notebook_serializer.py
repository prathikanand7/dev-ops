from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from jobs.models import Notebook

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Notebook Details Example',
            summary='A standard parsed notebook response',
            value={
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "name": "Data Analysis R Script",
                "description": "Runs basic regression on the input dataset.",
                "created_at": "2024-10-25T14:15:22Z",
                "notebook_file": "http://localhost:8000/media/notebooks/script.ipynb",
                "environment_file": "http://localhost:8000/media/environments/renv.lock",
                "parameter_schema": [
                    {"name": "dataset", "type": "string", "default": "data.csv"},
                    {"name": "iterations", "type": "number", "default": "100"}
                ]
            }
        )
    ]
)
class NotebookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notebook
        fields = ['id', 'name', 'description', 'created_at', 'notebook_file', 'environment_file', 'parameter_schema']
        read_only_fields = ['id', 'created_at', 'parameter_schema']
        extra_kwargs = {
            'parameter_schema': {
                'help_text': 'Automatically extracted JSON schema detailing the variables found in the first cell of the notebook.'
            },
            'notebook_file': {
                'help_text': 'The actual Jupyter/R notebook file to be executed.'
            }
        }