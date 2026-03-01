from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from jobs.models import Job, Notebook


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    View for displaying the user dashboard with their notebooks and jobs.
    """
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['notebooks'] = Notebook.objects.filter(owner=self.request.user).order_by('-created_at')
        context['jobs'] = Job.objects.filter(user=self.request.user).order_by('-created_at')
        return context