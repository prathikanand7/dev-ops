from pathlib import Path
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from jobs.models import Job, Notebook


FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "notebooks"


@override_settings(
    WORKER_CALLBACK_URL="http://testserver",
    WORKER_WEBHOOK_SECRET="lightweight-test-secret",
)
class NotebookProcessingLightE2ETestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="light-e2e-user", password="testpassword")
        self.token = Token.objects.create(user=self.user)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def _fixture_upload(self, filename):
        fixture_path = FIXTURES_DIR / filename
        with fixture_path.open("rb") as fixture:
            return SimpleUploadedFile(
                filename,
                fixture.read(),
                content_type="application/x-ipynb+json",
            )

    def _upload_notebook(self, name, fixture_name):
        response = self.client.post(
            reverse("notebook-list"),
            {"name": name, "notebook_file": self._fixture_upload(fixture_name)},
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.data)
        return Notebook.objects.get(id=response.data["id"]), response.data

    def test_upload_lightweight_examples_extract_expected_schema(self):
        notebook_a, _ = self._upload_notebook(
            "Lightweight Example A",
            "Notebook_Lightweight_Example_A.ipynb",
        )
        notebook_b, _ = self._upload_notebook(
            "Lightweight Example B",
            "Notebook_Lightweight_Example_B.ipynb",
        )

        self.assertEqual(
            notebook_a.parameter_schema,
            [
                {"name": "param_dataset", "default": "sample_input.csv", "type": "string"},
                {"name": "param_max_rows", "default": "100", "type": "number"},
                {"name": "param_make_plot", "default": "true", "type": "boolean"},
            ],
        )
        self.assertEqual(
            notebook_b.parameter_schema,
            [
                {"name": "param_region", "default": "coastal", "type": "string"},
                {"name": "param_depth_limit", "default": "2.75", "type": "number"},
                {"name": "param_include_qc", "default": "false", "type": "boolean"},
            ],
        )

    def test_run_example_a_standard_profile_dispatches_and_coerces_types(self):
        notebook, _ = self._upload_notebook(
            "Lightweight Example A",
            "Notebook_Lightweight_Example_A.ipynb",
        )
        upload = SimpleUploadedFile("tiny.csv", b"col1,col2\n1,2\n", content_type="text/csv")

        with (
            patch(
                "jobs.views.api_views.notebook_viewset.transaction.on_commit",
                side_effect=lambda fn: fn(),
            ) as mock_on_commit,
            patch("jobs.views.api_views.notebook_viewset.dispatch_job_task.delay") as mock_dispatch,
        ):
            response = self.client.post(
                reverse("notebook-run", args=[notebook.id]),
                {
                    "param_max_rows": "250",
                    "param_make_plot": "false",
                    "execution_profile": "standard",
                    "upload_01": upload,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, 202, response.data)
        self.assertEqual(response.data["execution_profile"], "standard")
        self.assertEqual(response.data["status"], "PENDING")

        job = Job.objects.get(id=response.data["job_id"])
        self.assertEqual(job.status, "PENDING")
        self.assertEqual(job.job_parameters["param_dataset"], "sample_input.csv")
        self.assertEqual(job.job_parameters["param_max_rows"], 250)
        self.assertIs(job.job_parameters["param_make_plot"], False)
        self.assertTrue(job.job_parameters["upload_01"].endswith(".csv"))
        self.assertIn("_download_upload_01", job.job_parameters)
        self.assertTrue(job.job_parameters["_download_upload_01"].startswith("http"))
        self.assertIn("/api_uploads/", job.job_parameters["_download_upload_01"])
        self.assertTrue(job.job_parameters["_download_upload_01"].endswith(".csv"))
        mock_on_commit.assert_called_once()
        mock_dispatch.assert_called_once_with(job.id)

    def test_run_example_b_ec2_profile_submits_batch_and_skips_k8s_dispatch(self):
        notebook, _ = self._upload_notebook(
            "Lightweight Example B",
            "Notebook_Lightweight_Example_B.ipynb",
        )
        upload = SimpleUploadedFile(
            "input_dataset.xlsx",
            b"fake-excel-bytes",
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        with (
            patch("jobs.views.api_views.notebook_viewset.dispatch_job_task.delay") as mock_dispatch,
            patch("jobs.views.api_views.notebook_viewset.submit_aws_batch_job") as mock_submit_aws,
        ):
            mock_submit_aws.return_value = {
                "batch_job_id": "batch-job-456",
                "job_id": "submission-job-456",
            }
            response = self.client.post(
                reverse("notebook-run", args=[notebook.id]),
                {
                    "execution_profile": "ec2_200gb",
                    "param_region": "offshore",
                    "param_01_input_data_filename": upload,
                },
                format="multipart",
            )

        self.assertEqual(response.status_code, 202, response.data)
        self.assertEqual(response.data["execution_profile"], "ec2_200gb")
        self.assertEqual(response.data["status"], "PROVISIONING")
        self.assertEqual(response.data["batch_job_id"], "batch-job-456")

        job = Job.objects.get(id=response.data["job_id"])
        self.assertEqual(job.status, "PROVISIONING")
        self.assertEqual(job.job_parameters["batch_job_id"], "batch-job-456")
        self.assertEqual(job.job_parameters["param_region"], "offshore")
        self.assertEqual(job.job_parameters["param_01_input_data_filename"], "input_dataset.xlsx")
        self.assertIn("_download_param_01_input_data_filename", job.job_parameters)
        self.assertTrue(job.job_parameters["_download_param_01_input_data_filename"].startswith("http"))
        self.assertIn("/api_uploads/", job.job_parameters["_download_param_01_input_data_filename"])
        self.assertTrue(job.job_parameters["_download_param_01_input_data_filename"].endswith(".xlsx"))

        submitted_payload = mock_submit_aws.call_args[0][1]
        self.assertEqual(submitted_payload["param_01_input_data_filename"], "input_dataset.xlsx")
        mock_dispatch.assert_not_called()

    def test_run_example_b_uses_schema_defaults_when_not_overridden(self):
        notebook, _ = self._upload_notebook(
            "Lightweight Example B",
            "Notebook_Lightweight_Example_B.ipynb",
        )

        with (
            patch(
                "jobs.views.api_views.notebook_viewset.transaction.on_commit",
                side_effect=lambda fn: fn(),
            ),
            patch("jobs.views.api_views.notebook_viewset.dispatch_job_task.delay") as mock_dispatch,
        ):
            response = self.client.post(
                reverse("notebook-run", args=[notebook.id]),
                {"execution_profile": "standard"},
                format="multipart",
            )

        self.assertEqual(response.status_code, 202, response.data)
        job = Job.objects.get(id=response.data["job_id"])
        self.assertEqual(job.job_parameters["param_region"], "coastal")
        self.assertEqual(job.job_parameters["param_depth_limit"], 2.75)
        self.assertIs(job.job_parameters["param_include_qc"], False)
        mock_dispatch.assert_called_once_with(job.id)

    def test_complete_endpoint_updates_job_for_lightweight_run(self):
        notebook, _ = self._upload_notebook(
            "Lightweight Example A",
            "Notebook_Lightweight_Example_A.ipynb",
        )
        job = Job.objects.create(
            notebook=notebook,
            user=self.user,
            status="RUNNING",
            job_parameters={"execution_profile": "standard"},
        )
        output_file = SimpleUploadedFile("result.txt", b"ok", content_type="text/plain")
        unauth_client = APIClient()

        response = unauth_client.post(
            reverse("job-complete", args=[job.id]),
            {"status": "SUCCESS", "logs": "Completed lightweight execution", "output_file": output_file},
            format="multipart",
            HTTP_X_WORKER_TOKEN="lightweight-test-secret",
        )

        self.assertEqual(response.status_code, 200, response.data)
        job.refresh_from_db()
        self.assertEqual(job.status, "SUCCESS")
        self.assertEqual(job.logs, "Completed lightweight execution")
        self.assertTrue(job.output_file.name.startswith("job_outputs/result"))
