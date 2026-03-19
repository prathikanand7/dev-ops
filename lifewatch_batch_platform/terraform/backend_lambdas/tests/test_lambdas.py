import json
import unittest
from datetime import datetime, timezone
from email.generator import BytesGenerator
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import Mock, patch

from bootstrap_aws_stubs import ClientError
import history_list
import lambda_function
import logs
import results
import status


def parse_body(lambda_response):
    return json.loads(lambda_response["body"])


def build_multipart_body(parts):
    msg = MIMEMultipart("form-data")
    for part in parts:
        payload = part.get("content", b"")
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        mime_part = MIMEApplication(payload)

        disposition = f'form-data; name="{part["name"]}"'
        if part.get("filename"):
            disposition += f'; filename="{part["filename"]}"'
        mime_part.add_header("Content-Disposition", disposition)
        if part.get("content_type"):
            mime_part.add_header("Content-Type", part["content_type"])

        msg.attach(mime_part)

    buff = BytesIO()
    generator = BytesGenerator(buff, mangle_from_=False, maxheaderlen=0)
    generator.flatten(msg)
    return msg.get("Content-Type"), buff.getvalue().decode("utf-8")


class TestSubmitLambda(unittest.TestCase):
    def test_lambda_handler_rejects_non_multipart(self):
        response = lambda_function.lambda_handler({"headers": {}, "body": "{}"}, None)
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            parse_body(response)["error"], "Request must be multipart/form-data"
        )

    def test_lambda_handler_submits_job_for_minimal_valid_payload(self):
        lambda_function.JOB_PROFILES_CONFIG = {
            "standard": {
                "queue": "queue-arn",
                "definition": "definition-arn",
            }
        }

        notebook = {
            "metadata": {"language_info": {"name": "python"}},
            "cells": [
                {
                    "cell_type": "code",
                    "source": [
                        "param_limit = 1\n",
                        "print('ok')\n",
                    ],
                }
            ],
        }

        content_type, body = build_multipart_body(
            [
                {
                    "name": "notebook",
                    "filename": "demo.ipynb",
                    "content_type": "application/json",
                    "content": json.dumps(notebook),
                },
                {
                    "name": "param_limit",
                    "content": "5",
                },
                {
                    "name": "execution_profile",
                    "content": "standard",
                },
            ]
        )

        s3_mock = Mock()
        batch_mock = Mock()
        batch_mock.submit_job.return_value = {"jobId": "batch-123"}

        with (
            patch.object(lambda_function, "s3", s3_mock),
            patch.object(lambda_function, "batch", batch_mock),
            patch.object(lambda_function.uuid, "uuid4", return_value="job-123"),
        ):
            response = lambda_function.lambda_handler(
                {
                    "headers": {"content-type": content_type},
                    "body": body,
                    "isBase64Encoded": False,
                },
                None,
            )

        payload = parse_body(response)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(payload["job_id"], "job-123")
        self.assertEqual(payload["execution_profile"], "standard")
        self.assertEqual(s3_mock.put_object.call_count, 2)
        batch_mock.submit_job.assert_called_once()

    def test_lambda_handler_rejects_missing_notebook_part(self):
        lambda_function.JOB_PROFILES_CONFIG = {
            "standard": {
                "queue": "queue-arn",
                "definition": "definition-arn",
            }
        }

        content_type, body = build_multipart_body(
            [
                {
                    "name": "param_limit",
                    "content": "5",
                },
                {
                    "name": "execution_profile",
                    "content": "standard",
                },
            ]
        )

        response = lambda_function.lambda_handler(
            {
                "headers": {"content-type": content_type},
                "body": body,
                "isBase64Encoded": False,
            },
            None,
        )

        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(
            parse_body(response)["error"], "Missing mandatory 'notebook' file."
        )

    def test_lambda_handler_uploads_environment_and_input_files(self):
        lambda_function.JOB_PROFILES_CONFIG = {
            "standard": {
                "queue": "queue-arn",
                "definition": "definition-arn",
            }
        }

        notebook = {
            "metadata": {"language_info": {"name": "python"}},
            "cells": [{"cell_type": "code", "source": ["param_limit = 1\n"]}],
        }

        content_type, body = build_multipart_body(
            [
                {
                    "name": "notebook",
                    "filename": "demo.ipynb",
                    "content_type": "application/json",
                    "content": json.dumps(notebook),
                },
                {
                    "name": "environment",
                    "filename": "environment.yaml",
                    "content_type": "text/yaml",
                    "content": "name: test-env\n",
                },
                {
                    "name": "dataset",
                    "filename": "input.csv",
                    "content_type": "text/csv",
                    "content": "a,b\n1,2\n",
                },
                {
                    "name": "execution_profile",
                    "content": "standard",
                },
            ]
        )

        s3_mock = Mock()
        batch_mock = Mock()
        batch_mock.submit_job.return_value = {"jobId": "batch-123"}

        with (
            patch.object(lambda_function, "s3", s3_mock),
            patch.object(lambda_function, "batch", batch_mock),
            patch.object(lambda_function.uuid, "uuid4", return_value="job-456"),
        ):
            response = lambda_function.lambda_handler(
                {
                    "headers": {"content-type": content_type},
                    "body": body,
                    "isBase64Encoded": False,
                },
                None,
            )

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(s3_mock.put_object.call_count, 4)

        uploaded_keys = [
            call.kwargs["Key"] for call in s3_mock.put_object.call_args_list
        ]
        self.assertIn("jobs/job-456/environment.yaml", uploaded_keys)
        self.assertIn("jobs/job-456/inputs/input.csv", uploaded_keys)


class TestStatusLambda(unittest.TestCase):
    def test_missing_job_id(self):
        response = status.lambda_handler({"pathParameters": {}}, None)
        self.assertEqual(response["statusCode"], 400)

    def test_successful_status_lookup(self):
        body_mock = Mock()
        body_mock.read.return_value = b'{"batch_job_id": "batch-abc"}'

        s3_mock = Mock()
        s3_mock.get_object.return_value = {"Body": body_mock}

        batch_mock = Mock()
        batch_mock.describe_jobs.return_value = {
            "jobs": [
                {
                    "jobName": "job-1",
                    "status": "SUCCEEDED",
                    "createdAt": 1,
                    "startedAt": 2,
                    "stoppedAt": 3,
                }
            ]
        }

        with (
            patch.object(status, "s3", s3_mock),
            patch.object(status, "batch", batch_mock),
        ):
            response = status.lambda_handler(
                {"pathParameters": {"job_id": "job-1"}}, None
            )

        payload = parse_body(response)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(payload["status"], "SUCCEEDED")

    def test_returns_404_when_batch_job_missing(self):
        body_mock = Mock()
        body_mock.read.return_value = b'{"batch_job_id": "batch-abc"}'

        s3_mock = Mock()
        s3_mock.get_object.return_value = {"Body": body_mock}

        batch_mock = Mock()
        batch_mock.describe_jobs.return_value = {"jobs": []}

        with (
            patch.object(status, "s3", s3_mock),
            patch.object(status, "batch", batch_mock),
        ):
            response = status.lambda_handler(
                {"pathParameters": {"job_id": "job-1"}}, None
            )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(parse_body(response)["error"], "Batch Job not found in AWS")


class TestLogsLambda(unittest.TestCase):
    def test_missing_job_id_returns_400(self):
        response = logs.lambda_handler({"pathParameters": {}}, None)
        self.assertEqual(response["statusCode"], 400)

    def test_returns_404_when_batch_job_missing(self):
        body_mock = Mock()
        body_mock.read.return_value = b'{"batch_job_id": "batch-abc"}'

        s3_mock = Mock()
        s3_mock.get_object.return_value = {"Body": body_mock}

        batch_mock = Mock()
        batch_mock.describe_jobs.return_value = {"jobs": []}

        with (
            patch.object(logs, "s3", s3_mock),
            patch.object(logs, "batch_client", batch_mock),
        ):
            response = logs.lambda_handler(
                {"pathParameters": {"job_id": "job-1"}}, None
            )

        self.assertEqual(response["statusCode"], 404)
        self.assertEqual(parse_body(response)["error"], "Batch Job not found in AWS")

    def test_returns_404_when_log_stream_missing(self):
        body_mock = Mock()
        body_mock.read.return_value = b'{"batch_job_id": "batch-abc"}'

        s3_mock = Mock()
        s3_mock.get_object.return_value = {"Body": body_mock}

        batch_mock = Mock()
        batch_mock.describe_jobs.return_value = {"jobs": [{"container": {}}]}

        with (
            patch.object(logs, "s3", s3_mock),
            patch.object(logs, "batch_client", batch_mock),
        ):
            response = logs.lambda_handler(
                {"pathParameters": {"job_id": "job-1"}}, None
            )

        self.assertEqual(response["statusCode"], 404)

    def test_returns_log_messages(self):
        body_mock = Mock()
        body_mock.read.return_value = b'{"batch_job_id": "batch-abc"}'

        s3_mock = Mock()
        s3_mock.get_object.return_value = {"Body": body_mock}

        batch_mock = Mock()
        batch_mock.describe_jobs.return_value = {
            "jobs": [{"container": {"logStreamName": "stream-1"}}]
        }

        logs_client_mock = Mock()
        logs_client_mock.get_log_events.return_value = {
            "events": [{"message": "line-1"}, {"message": "line-2"}]
        }

        with (
            patch.object(logs, "s3", s3_mock),
            patch.object(logs, "batch_client", batch_mock),
            patch.object(logs, "logs_client", logs_client_mock),
        ):
            response = logs.lambda_handler(
                {"pathParameters": {"job_id": "job-1"}}, None
            )

        payload = parse_body(response)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(payload["logs"], ["line-1", "line-2"])


class TestResultsLambda(unittest.TestCase):
    def test_missing_job_id_returns_400(self):
        response = results.lambda_handler({"pathParameters": {}}, None)
        self.assertEqual(response["statusCode"], 400)

    def test_returns_success_presigned_url_when_outputs_zip_exists(self):
        s3_mock = Mock()
        s3_mock.generate_presigned_url.return_value = "https://example/download"

        with patch.object(results, "s3", s3_mock):
            response = results.lambda_handler(
                {"pathParameters": {"job_id": "job-1"}}, None
            )

        payload = parse_body(response)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(payload["status"], "success")

    def test_falls_back_to_failed_outputs(self):
        not_found_error = ClientError(
            {"Error": {"Code": "404", "Message": "Not found"}},
            "HeadObject",
        )

        s3_mock = Mock()
        s3_mock.head_object.side_effect = [not_found_error, None]
        s3_mock.generate_presigned_url.return_value = "https://example/download-failed"

        with patch.object(results, "s3", s3_mock):
            response = results.lambda_handler(
                {"pathParameters": {"job_id": "job-1"}}, None
            )

        payload = parse_body(response)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(payload["status"], "partial_failure")

    def test_returns_404_when_no_outputs_exist(self):
        not_found_error = ClientError(
            {"Error": {"Code": "404", "Message": "Not found"}},
            "HeadObject",
        )

        s3_mock = Mock()
        s3_mock.head_object.side_effect = [not_found_error, not_found_error]

        with patch.object(results, "s3", s3_mock):
            response = results.lambda_handler(
                {"pathParameters": {"job_id": "job-1"}}, None
            )

        self.assertEqual(response["statusCode"], 404)
        self.assertIn("No outputs found for job job-1", parse_body(response)["error"])


class TestHistoryListLambda(unittest.TestCase):
    def test_builds_history_items_and_maps_batch_status(self):
        body_mock = Mock()
        body_mock.read.return_value = (
            b'{"batch_job_id": "batch-abc", "execution_profile": "standard"}'
        )

        s3_mock = Mock()
        paginator_mock = Mock()
        paginator_mock.paginate.return_value = [
            {"CommonPrefixes": [{"Prefix": "jobs/job-1/"}]}
        ]
        s3_mock.get_paginator.return_value = paginator_mock
        s3_mock.get_object.return_value = {
            "Body": body_mock,
            "LastModified": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }

        no_such_key = type("NoSuchKey", (Exception,), {})
        s3_mock.exceptions = SimpleNamespace(NoSuchKey=no_such_key)

        batch_mock = Mock()
        batch_mock.describe_jobs.return_value = {
            "jobs": [
                {
                    "jobId": "batch-abc",
                    "status": "FAILED",
                    "statusReason": "Container crashed",
                }
            ]
        }

        with (
            patch.object(history_list, "s3", s3_mock),
            patch.object(history_list, "batch", batch_mock),
        ):
            response = history_list.lambda_handler({}, None)

        payload = parse_body(response)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(len(payload["jobs"]), 1)
        self.assertEqual(payload["jobs"][0]["status"], "FAILED")
        self.assertEqual(payload["jobs"][0]["error"], "Container crashed")

    def test_maps_non_failed_status_reason_to_info(self):
        body_mock = Mock()
        body_mock.read.return_value = (
            b'{"batch_job_id": "batch-abc", "execution_profile": "standard"}'
        )

        s3_mock = Mock()
        paginator_mock = Mock()
        paginator_mock.paginate.return_value = [
            {"CommonPrefixes": [{"Prefix": "jobs/job-2/"}]}
        ]
        s3_mock.get_paginator.return_value = paginator_mock
        s3_mock.get_object.return_value = {
            "Body": body_mock,
            "LastModified": datetime(2026, 1, 2, tzinfo=timezone.utc),
        }

        no_such_key = type("NoSuchKey", (Exception,), {})
        s3_mock.exceptions = SimpleNamespace(NoSuchKey=no_such_key)

        batch_mock = Mock()
        batch_mock.describe_jobs.return_value = {
            "jobs": [
                {
                    "jobId": "batch-abc",
                    "status": "RUNNING",
                    "statusReason": "Starting container",
                }
            ]
        }

        with (
            patch.object(history_list, "s3", s3_mock),
            patch.object(history_list, "batch", batch_mock),
        ):
            response = history_list.lambda_handler({}, None)

        payload = parse_body(response)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(payload["jobs"][0]["status"], "RUNNING")
        self.assertEqual(payload["jobs"][0]["info"], "Starting container")


if __name__ == "__main__":
    unittest.main()
