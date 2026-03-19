import os
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import Mock


class ClientError(Exception):
    def __init__(self, error_response, operation_name):
        super().__init__(str(error_response))
        self.response = error_response
        self.operation_name = operation_name


os.environ.setdefault("BUCKET", "test-bucket")

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

fake_boto3 = ModuleType("boto3")
fake_boto3.client = lambda _service_name: Mock()
sys.modules["boto3"] = fake_boto3

fake_botocore_exceptions = ModuleType("botocore.exceptions")
fake_botocore_exceptions.ClientError = ClientError
fake_botocore = ModuleType("botocore")
fake_botocore.exceptions = fake_botocore_exceptions
sys.modules["botocore"] = fake_botocore
sys.modules["botocore.exceptions"] = fake_botocore_exceptions
