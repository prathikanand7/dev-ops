from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy

from jobs.models import Notebook
from jobs.forms import NotebookUploadForm
from jobs.utils import parse_notebook_parameters

class NotebookUploadView(LoginRequiredMixin, CreateView):
    """
    View for uploading a new notebook.
    """
    model = Notebook
    form_class = NotebookUploadForm
    template_name = 'upload.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        extracted_params = parse_notebook_parameters(self.request.FILES['notebook_file'])
        form.instance.parameter_schema = extracted_params
        return super().form_valid(form)