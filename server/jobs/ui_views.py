from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy

from .models import Job, Notebook
from .forms import NotebookUploadForm
from .utils import parse_notebook_parameters

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notebooks'] = Notebook.objects.filter(owner=self.request.user).order_by('-created_at')
        context['jobs'] = Job.objects.filter(user=self.request.user).order_by('-created_at')
        return context

class NotebookUploadView(LoginRequiredMixin, CreateView):
    model = Notebook
    form_class = NotebookUploadForm
    template_name = 'upload.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        extracted_params = parse_notebook_parameters(self.request.FILES['notebook_file'])
        form.instance.parameter_schema = extracted_params
        return super().form_valid(form)