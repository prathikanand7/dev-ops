from django import forms
from .models import Notebook

class NotebookUploadForm(forms.ModelForm):
    class Meta:
        model = Notebook
        fields = ['name', 'description', 'notebook_file', 'environment_file']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }