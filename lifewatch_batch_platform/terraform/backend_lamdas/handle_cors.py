import json
from typing import Any, Dict

DEFAULT_HEADERS: Dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,x-api-key,Authorization",
    "Access-Control-Allow-Methods": "OPTIONS,GET,POST",
    "Content-Type": "application/json",
}


def response(status_code: int, body: Any, headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    payload = body if isinstance(body, str) else json.dumps(body)
    return {
        "statusCode": status_code,
        "headers": headers or DEFAULT_HEADERS,
        "body": payload,
    }
