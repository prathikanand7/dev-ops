"""Resolve API base URL from environment first, then Terraform output fallback."""

import os
import subprocess

def fetch_api_url() -> str:
    env_url = os.getenv("LIFEWATCH_API_URL", "").strip()
    if env_url:
        return env_url
    try:
        dev_dir = os.path.join(os.path.dirname(__file__), "..", "environments", "dev")
        url = subprocess.check_output(
            ["terraform", "output", "-raw", "api_gateway_url"],
            cwd=os.path.abspath(dev_dir),
            text=True,
        ).strip()
        if url:
            return url
    except Exception:
        pass
    raise RuntimeError("Unable to resolve API URL. Set LIFEWATCH_API_URL or run terraform output first.")
