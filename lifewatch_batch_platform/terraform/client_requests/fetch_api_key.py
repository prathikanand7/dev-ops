import os
import subprocess

def fetch_api_key() -> str:
    env_key = os.getenv("LIFEWATCH_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        dev_dir = os.path.join(os.path.dirname(__file__), "..", "environments", "dev")
        key = subprocess.check_output(
            ["terraform", "output", "-raw", "api_key"],
            cwd=os.path.abspath(dev_dir),
            text=True,
        ).strip()
        if key:
            return key
    except Exception:
        pass
    raise RuntimeError("Unable to resolve API key. Set LIFEWATCH_API_KEY or run terraform output first.")