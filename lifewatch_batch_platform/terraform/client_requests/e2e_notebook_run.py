#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run an end-to-end AWS Batch notebook execution test against the deployed API."
    )
    parser.add_argument("--api-base-url", required=True, help="API base URL, e.g. https://.../dev")
    parser.add_argument("--api-key", required=True, help="API key used in x-api-key header")
    parser.add_argument("--notebook-path", required=True, help="Path to notebook .ipynb")
    parser.add_argument("--data-file-path", required=True, help="Path to main data input file")
    parser.add_argument("--environment-path", required=True, help="Path to environment.yaml")
    parser.add_argument(
        "--execution-profile",
        default="ec2_200gb",
        choices=["standard", "ec2_200gb"],
        help="Batch execution profile",
    )
    parser.add_argument("--poll-interval-seconds", type=int, default=20, help="Polling interval in seconds")
    parser.add_argument("--timeout-seconds", type=int, default=3600, help="Overall timeout in seconds")
    parser.add_argument(
        "--output-dir",
        default="lifewatch_batch_platform/terraform/environments/dev/e2e_outputs",
        help="Folder where downloaded outputs and logs are stored",
    )
    parser.add_argument(
        "--submit-max-attempts",
        type=int,
        default=12,
        help="How many times to retry notebook submission on transient API errors",
    )
    parser.add_argument(
        "--submit-retry-seconds",
        type=int,
        default=10,
        help="Seconds to wait between submission retries",
    )
    return parser.parse_args()


def request_json(
    method,
    url,
    headers,
    retries=1,
    retry_delay_seconds=5,
    retry_on_statuses=None,
    **kwargs,
):
    retry_on_statuses = set(retry_on_statuses or [])
    last_error = None

    for attempt in range(1, retries + 1):
        response = requests.request(method, url, headers=headers, timeout=120, **kwargs)
        body_text = response.text

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError(f"Non-JSON response from {url} ({response.status_code}): {body_text}") from exc

        if response.status_code < 400:
            return payload

        can_retry = response.status_code in retry_on_statuses and attempt < retries
        if can_retry:
            print(
                f"Transient API error from {url} ({response.status_code}) on attempt {attempt}/{retries}; retrying in {retry_delay_seconds}s ..."
            )
            time.sleep(retry_delay_seconds)
            last_error = RuntimeError(f"API error from {url} ({response.status_code}): {payload}")
            continue

        raise RuntimeError(f"API error from {url} ({response.status_code}): {payload}")

    if last_error:
        raise last_error
    raise RuntimeError(f"Failed request to {url} without a captured error state.")


def submit_job(args, headers):
    submit_url = f"{args.api_base_url.rstrip('/')}/batch/jobs"
    print(f"Submitting notebook job to {submit_url} using profile={args.execution_profile} ...")

    with (
        open(args.notebook_path, "rb") as notebook_file,
        open(args.data_file_path, "rb") as data_file,
        open(args.environment_path, "rb") as env_file,
    ):
        files = {
            "notebook": (os.path.basename(args.notebook_path), notebook_file.read(), "application/x-ipynb+json"),
            "upload_01": (
                os.path.basename(args.data_file_path),
                data_file.read(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ),
            "environment": (os.path.basename(args.environment_path), env_file.read(), "application/x-yaml"),
            # Notebook parameters used in the current demo flow
            "param_01_input_data_filename": (None, os.path.basename(args.data_file_path)),
            "param_02_input_data_sheet": (None, "BIRDS"),
            "param_03_input_metadata_sheet": (None, "METADATA"),
            "param_04_output_samples_ecological_parameters": (None, "false"),
            "param_05_output_make_plots": (None, "true"),
            "param_07_first_month": (None, "1"),
            "param_10_upper_limit_max_depth": (None, "0"),
            "execution_profile": (None, args.execution_profile),
        }
        payload = request_json(
            "POST",
            submit_url,
            headers,
            files=files,
            retries=args.submit_max_attempts,
            retry_delay_seconds=args.submit_retry_seconds,
            retry_on_statuses={403, 429, 500, 502, 503, 504},
        )

    # New AWS Lambda flow returns only job_id.
    # Older backend flow returned both job_id and batch_job_id.
    notebook_job_id = payload.get("job_id")
    batch_job_id = payload.get("batch_job_id")
    if not notebook_job_id:
        raise RuntimeError(f"Submit response missing job_id: {payload}")

    if batch_job_id:
        print(f"Submitted OK. notebook_job_id={notebook_job_id} batch_job_id={batch_job_id}")
    else:
        print(f"Submitted OK. notebook_job_id={notebook_job_id}")
    return payload, notebook_job_id, batch_job_id


def _fetch_with_candidate_ids(api_base_url, headers, endpoint_suffix, candidate_ids):
    last_error = None
    for candidate_id in candidate_ids:
        url = f"{api_base_url.rstrip('/')}/batch/jobs/{candidate_id}{endpoint_suffix}"
        try:
            payload = request_json("GET", url, headers)
            return candidate_id, payload
        except RuntimeError as exc:
            # Try the next candidate when an endpoint cannot resolve the ID.
            if "(404)" in str(exc):
                last_error = exc
                continue
            raise
    if last_error:
        raise last_error
    raise RuntimeError("No candidate IDs available for endpoint lookup.")


def poll_batch_status(api_base_url, headers, candidate_ids, poll_interval, timeout_seconds):
    active_status_id = None
    deadline = time.time() + timeout_seconds
    last_status = None
    status_payload = {}

    print("Polling batch status ...")
    while time.time() < deadline:
        if active_status_id:
            status_url = f"{api_base_url.rstrip('/')}/batch/jobs/{active_status_id}"
            status_payload = request_json("GET", status_url, headers)
        else:
            active_status_id, status_payload = _fetch_with_candidate_ids(
                api_base_url, headers, "", candidate_ids
            )

        status = status_payload.get("status", "UNKNOWN")
        if status != last_status:
            print(f"Current batch status: {status}")
            last_status = status

        if status in {"SUCCEEDED", "FAILED"}:
            return status_payload, active_status_id

        time.sleep(poll_interval)

    raise TimeoutError(
        f"Timed out after {timeout_seconds}s waiting for batch job status. tried_ids={candidate_ids}"
    )


def get_logs(api_base_url, headers, candidate_ids):
    _, logs_payload = _fetch_with_candidate_ids(api_base_url, headers, "/logs", candidate_ids)
    raw_logs = logs_payload.get("logs", "")
    if isinstance(raw_logs, list):
        return "\n".join(str(line) for line in raw_logs)
    return str(raw_logs)


def download_results(api_base_url, headers, candidate_ids, output_dir):
    result_lookup_id, results_payload = _fetch_with_candidate_ids(
        api_base_url, headers, "/results", candidate_ids
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files = []

    # Legacy flow: base64-embedded files.
    results = results_payload.get("results")
    if isinstance(results, list) and results:
        for entry in results:
            filename = entry.get("filename")
            content_base64 = entry.get("content_base64")
            if not filename or not content_base64:
                raise RuntimeError(f"Malformed result entry: {entry}")

            file_path = output_dir / filename
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_bytes = base64.b64decode(content_base64)
            file_path.write_bytes(file_bytes)
            written_files.append(str(file_path))
            print(f"Wrote result file: {file_path}")
        return results_payload, written_files

    # Current AWS Lambda flow: pre-signed download URL to outputs.zip.
    download_url = results_payload.get("download_url")
    if not download_url:
        raise RuntimeError(
            f"No downloadable results found for lookup_id={result_lookup_id}. payload={results_payload}"
        )

    parsed = urlparse(download_url)
    inferred_name = os.path.basename(parsed.path) or f"{result_lookup_id}_outputs.zip"
    archive_path = output_dir / inferred_name
    download_response = requests.get(download_url, timeout=300)
    if download_response.status_code >= 400:
        raise RuntimeError(
            f"Failed to download results archive ({download_response.status_code}) from {download_url}"
        )
    archive_path.write_bytes(download_response.content)
    written_files.append(str(archive_path))
    print(f"Wrote result archive: {archive_path}")

    return results_payload, written_files


def main():
    args = parse_args()
    headers = {"x-api-key": args.api_key, "Accept": "application/json"}

    notebook_path = Path(args.notebook_path)
    data_path = Path(args.data_file_path)
    env_path = Path(args.environment_path)
    for required_file in [notebook_path, data_path, env_path]:
        if not required_file.exists():
            print(f"Missing required file: {required_file}", file=sys.stderr)
            return 2

    base_output = Path(args.output_dir)

    submit_payload, notebook_job_id, batch_job_id = submit_job(args, headers)
    status_candidate_ids = [id_ for id_ in [notebook_job_id, batch_job_id] if id_]
    status_payload, status_lookup_id = poll_batch_status(
        args.api_base_url,
        headers,
        status_candidate_ids,
        args.poll_interval_seconds,
        args.timeout_seconds,
    )

    status = status_payload.get("status", "UNKNOWN")
    job_output_dir = base_output / notebook_job_id
    job_output_dir.mkdir(parents=True, exist_ok=True)

    logs_candidate_ids = [id_ for id_ in [status_lookup_id, notebook_job_id, batch_job_id] if id_]
    logs_text = get_logs(args.api_base_url, headers, logs_candidate_ids)
    (job_output_dir / "batch_logs.txt").write_text(logs_text, encoding="utf-8")
    print(f"Saved logs to {job_output_dir / 'batch_logs.txt'}")

    if status != "SUCCEEDED":
        print(f"E2E FAILED: batch status is {status}", file=sys.stderr)
        print("Recent logs:")
        print(logs_text[-4000:])
        return 1

    results_payload, written_files = download_results(
        args.api_base_url,
        headers,
        [id_ for id_ in [notebook_job_id, status_lookup_id, batch_job_id] if id_],
        job_output_dir / "results",
    )

    summary = {
        "submit_payload": submit_payload,
        "status_payload": status_payload,
        "results_count": len(results_payload.get("results", [])),
        "written_files": written_files,
    }
    (job_output_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"E2E SUCCESS. Summary saved to {job_output_dir / 'summary.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
