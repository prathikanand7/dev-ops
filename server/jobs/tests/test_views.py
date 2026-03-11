from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from django.conf import settings
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

    @patch('jobs.views.ui_views.notebook_upload_view.parse_notebook_parameters')
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
        """Test the webhook updates job status only with the correct shared secret."""
        output_file = SimpleUploadedFile("output.csv", b"data")
        unauth_client = APIClient()
        
        # Test rejection (No token provided)
        fail_response_no_token = unauth_client.post(reverse('job-complete', args=[self.job.id]), {
            'status': 'SUCCESS',
            'logs': 'Executed perfectly',
            'output_file': output_file
        }, format='multipart')
        
        self.assertEqual(fail_response_no_token.status_code, 403)
        
        # Test rejection (Wrong token provided)
        fail_response_wrong_token = unauth_client.post(
            reverse('job-complete', args=[self.job.id]), 
            {'status': 'SUCCESS'}, 
            format='multipart',
            HTTP_X_WORKER_TOKEN='some-invalid-hacker-token'
        )
        
        self.assertEqual(fail_response_wrong_token.status_code, 403)

        # Test success (Correct token provided)
        success_response = unauth_client.post(
            reverse('job-complete', args=[self.job.id]), 
            {
                'status': 'SUCCESS',
                'logs': 'Executed perfectly',
                'output_file': output_file
            }, 
            format='multipart',
            HTTP_X_WORKER_TOKEN=settings.WORKER_WEBHOOK_SECRET
        )
        
        self.assertEqual(success_response.status_code, 200)
        
        # Verify database updates
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'SUCCESS')
        self.assertEqual(self.job.logs, 'Executed perfectly')
        self.assertTrue(self.job.output_file.name.startswith('job_outputs/output'))

    @patch('django.db.transaction.on_commit', side_effect=lambda f: f())
    @patch('jobs.views.api_views.notebook_viewset.dispatch_job_task.delay')
    @patch('jobs.utils.parse_notebook_parameters_from_payload')
    def test_trigger_notebook_api(self, mock_parse_payload, mock_dispatch, mock_on_commit):
        """Test triggering a notebook run and job creation."""
        mock_parse_payload.return_value = {"x": 5}
        
        url = reverse('notebook-run', args=[self.notebook.id]) 
        response = self.client.post(url, {'x': 5}, format='multipart')
        
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['status'], 'PENDING')
        self.assertEqual(response.data['execution_profile'], 'standard')
        
        job = Job.objects.get(id=response.data['job_id'])
        self.assertEqual(job.job_parameters, {"x": 5, "execution_profile": "standard"})
        mock_dispatch.assert_called_once_with(job.id)

    @patch('jobs.views.api_views.notebook_viewset.dispatch_job_task.delay')
    @patch('jobs.utils.parse_notebook_parameters_from_payload')
    def test_trigger_notebook_api_invalid_execution_profile(self, mock_parse_payload, mock_dispatch):
        """Test invalid execution profile is rejected with HTTP 400."""
        mock_parse_payload.return_value = {"x": 5}

        url = reverse('notebook-run', args=[self.notebook.id])
        response = self.client.post(
            url,
            {'x': 5, 'execution_profile': 'invalid-profile'},
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid execution_profile', response.data['error'])
        mock_dispatch.assert_not_called()

    @patch('jobs.views.api_views.notebook_viewset.dispatch_job_task.delay')
    @patch('jobs.views.api_views.notebook_viewset.submit_aws_batch_job')
    @patch('jobs.utils.parse_notebook_parameters_from_payload')
    def test_trigger_notebook_api_ec2_profile(self, mock_parse_payload, mock_submit_aws, mock_dispatch):
        """Test ec2_200gb profile submits to AWS Batch bridge and skips Kubernetes dispatch."""
        mock_parse_payload.return_value = {"x": 5}
        mock_submit_aws.return_value = {
            "batch_job_id": "aws-batch-job-123",
            "job_id": "payload-job-id-123"
        }
        upload = SimpleUploadedFile(
            "Template_MBO_Example_raw_v3.xlsx",
            b"fake-excel-bytes",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        url = reverse('notebook-run', args=[self.notebook.id])
        response = self.client.post(
            url,
            {
                'x': 5,
                'execution_profile': 'ec2_200gb',
                'param_01_input_data_filename': upload,
            },
            format='multipart'
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['execution_profile'], 'ec2_200gb')
        self.assertEqual(response.data['status'], 'PROVISIONING')
        self.assertEqual(response.data['batch_job_id'], 'aws-batch-job-123')

        job = Job.objects.get(id=response.data['job_id'])
        self.assertEqual(job.status, 'PROVISIONING')
        self.assertEqual(job.job_parameters['execution_profile'], 'ec2_200gb')
        self.assertEqual(job.job_parameters['batch_job_id'], 'aws-batch-job-123')
        self.assertEqual(
            job.job_parameters['param_01_input_data_filename'],
            'Template_MBO_Example_raw_v3.xlsx'
        )

        submit_payload = mock_submit_aws.call_args[0][1]
        self.assertEqual(
            submit_payload['param_01_input_data_filename'],
            'Template_MBO_Example_raw_v3.xlsx'
        )
        mock_dispatch.assert_not_called()

    @patch('jobs.views.api_views.job_viewset.boto3.client')
    def test_job_status_action_refreshes_batch_job(self, mock_boto3_client):
        """Test /api/jobs/<id>/status/ refreshes AWS Batch-backed jobs."""
        class FakeBatchClient:
            def describe_jobs(self, jobs):
                return {
                    "jobs": [{
                        "status": "SUCCEEDED",
                        "container": {"logStreamName": "demo/log/stream"}
                    }]
                }

        mock_boto3_client.return_value = FakeBatchClient()
        job = Job.objects.create(
            notebook=self.notebook,
            user=self.user,
            status='PENDING',
            job_parameters={
                "execution_profile": "ec2_200gb",
                "batch_job_id": "aws-batch-job-123"
            }
        )

        url = reverse('job-status', args=[job.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'SUCCESS')
        self.assertEqual(response.data['job_id'], str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, 'SUCCESS')

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
