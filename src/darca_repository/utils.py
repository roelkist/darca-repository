# darca_repository/utils.py
# License: MIT

import os
from typing import Optional


def expand_env_var(value: str) -> str:
    """
    Expand environment variables in the format ${VAR_NAME} inside a string.

    Example:
        input: "s3://${AWS_BUCKET}/backup"
        output (assuming AWS_BUCKET=my-bucket): "s3://my-bucket/backup"
    """
    if not isinstance(value, str):
        return value

    while "${" in value and "}" in value:
        start = value.find("${")
        end = value.find("}", start)
        if start == -1 or end == -1:
            break

        var_name = value[start + 2:end]
        var_value = os.getenv(var_name, "")
        value = value[:start] + var_value + value[end + 1:]

    return value


def get_env_or_default(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get the environment variable by key or return the default if not set.
    """
    return os.getenv(key, default)
