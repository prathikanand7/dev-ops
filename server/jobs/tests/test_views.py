from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from jobs.models import Notebook, Job

class WebViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        
        self.notebook_file = SimpleUploadedFile(
            "test_notebook.ipynb", 
            b"{\"cells\": []}", 
            content_type="application/x-ipynb+json"
        )
        self.notebook = Notebook.objects.create(
            owner=self.user,
            name="Test Notebook",
            notebook_file=self.notebook_file
        )
        
        self.job = Job.objects.create(
            notebook=self.notebook,
            user=self.user,
            status='PENDING',
            logs='Initial logs'
        )

    def test_dashboard_view(self):
        """Test the dashboard loads correctly with user's notebooks and jobs."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('notebooks', response.context)
        self.assertIn('jobs', response.context)
        self.assertEqual(len(response.context['notebooks']), 1)
        self.assertEqual(len(response.context['jobs']), 1)

    @patch('jobs.views.ui_views.parse_notebook_parameters')
    def test_upload_notebook(self, mock_parse_params):
        """Test notebook upload UI and parameter extraction."""
        mock_parse_params.return_value = [{"name": "param1", "type": "int"}]
        
        upload_file = SimpleUploadedFile("upload.ipynb", b"content")
        response = self.client.post(reverse('upload_notebook'), {
            'name': 'New Uploaded Notebook',
            'notebook_file': upload_file
        })
        
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Notebook.objects.filter(name='New Uploaded Notebook').exists())
        
        new_nb = Notebook.objects.get(name='New Uploaded Notebook')
        self.assertEqual(new_nb.parameter_schema, [{"name": "param1", "type": "int"}])


class APIViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apiuser', password='testpassword')
        self.token = Token.objects.create(user=self.user)
        
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.notebook_file = SimpleUploadedFile(
            "test_notebook.ipynb", b"{\"cells\": []}", content_type="application/x-ipynb+json"
        )
        self.notebook = Notebook.objects.create(
            owner=self.user,
            name="API Test Notebook",
            notebook_file=self.notebook_file,
            parameter_schema=[{"name": "x", "type": "int"}]
        )
        
        self.job = Job.objects.create(
            notebook=self.notebook,
            user=self.user,
            status='PENDING',
            logs='Initial logs'
        )

    def test_check_token_status(self):
        """Test token status returns true when token exists."""
        response = self.client.get(reverse('token_status'))
        self.assertTrue(response.json()['has_token'])

    def test_generate_new_token(self):
        """Test generating a new DRF token."""
        response = self.client.post(reverse('generate_token')) 
        self.assertEqual(response.status_code, 201)
        self.assertIn('token', response.json())

    def test_delete_notebook(self):
        """Test ModelViewSet DELETE notebook."""
        # DRF Router creates 'notebook-detail' URL name
        response = self.client.delete(reverse('notebook-detail', args=[self.notebook.id]))
        # DRF returns 204 No Content for successful deletions
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Notebook.objects.filter(id=self.notebook.id).exists())

    def test_delete_job(self):
        """Test ModelViewSet DELETE job."""
        response = self.client.delete(reverse('job-detail', args=[self.job.id]))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Job.objects.filter(id=self.job.id).exists())

    def test_poll_job_statuses(self):
        """Test the polling endpoint returns correct live job data."""
        # Custom actions use snake_case to kebab-case translation in URL names
        response = self.client.get(reverse('job-poll-status'))
        self.assertEqual(response.status_code, 200)
        jobs_data = response.json().get('jobs', [])
        self.assertEqual(len(jobs_data), 1)
        self.assertEqual(jobs_data[0]['id'], str(self.job.id))
        self.assertEqual(jobs_data[0]['status'], 'PENDING')

    def test_get_job_logs(self):
        """Test retrieving raw text logs via custom action."""
        response = self.client.get(reverse('job-logs', args=[self.job.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get('logs'), 'Initial logs')

    def test_job_complete_callback(self):
        """Test the unauthenticated webhook updates job status."""
        output_file = SimpleUploadedFile("output.csv", b"data")
        
        # We must use an unauthenticated client to test webhook bypass
        unauth_client = APIClient()
        response = unauth_client.post(reverse('job-complete', args=[self.job.id]), {
            'status': 'SUCCESS',
            'logs': 'Executed perfectly',
            'output_file': output_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, 200)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'SUCCESS')
        self.assertEqual(self.job.logs, 'Executed perfectly')
        self.assertTrue(self.job.output_file.name.startswith('job_outputs/output'))

    @patch('django.db.transaction.on_commit', side_effect=lambda f: f())
    @patch('jobs.views.api_views.dispatch_job_task.delay')
    @patch('jobs.views.api_views.parse_notebook_parameters_from_payload')
    def test_trigger_notebook_api(self, mock_parse_payload, mock_dispatch, mock_on_commit):
        """Test triggering a notebook run and job creation."""
        mock_parse_payload.return_value = {"x": 5}
        
        url = reverse('notebook-run', args=[self.notebook.id]) 
        response = self.client.post(url, {'x': 5}, format='multipart')
        
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['status'], 'PENDING')
        
        job = Job.objects.get(id=response.data['job_id'])
        self.assertEqual(job.job_parameters, {"x": 5})
        mock_dispatch.assert_called_once_with(job.id)

    def test_job_status_api_view(self):
        """Test retrieving job detail via ModelViewSet GET."""
        job = Job.objects.create(
            notebook=self.notebook,
            user=self.user,
            status='SUCCESS',
            logs='Test logs'
        )
        
        output_file = SimpleUploadedFile("result.txt", b"done")
        job.output_file = output_file
        job.save()

        # Hits the default GET /api/jobs/<id>/ provided by DRF ModelViewSet
        url = reverse('job-detail', args=[job.id]) 
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertEqual(response.data['logs'], 'Test logs')
        # DRF automatically formats FileFields as full absolute URLs
        self.assertIsNotNone(response.data['output_file'])