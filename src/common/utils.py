import hashlib
import json
from typing import Any

def calculate_hash(data: Any) -> str:
    """Calculate MD5 hash of data."""
    if isinstance(data, dict):
        data_str = json.dumps(data, sort_keys=True)
    else:
        data_str = str(data)
    return hashlib.md5(data_str.encode()).hexdigest()
