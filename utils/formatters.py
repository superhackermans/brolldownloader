"""Output formatting helpers."""
import json


def format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS format."""
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"


def timestamp_to_seconds(ts: str) -> int:
    """Convert MM:SS to seconds."""
    parts = ts.split(':')
    if len(parts) == 2:
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            return 0
    return 0


def pretty_json(obj, indent=2) -> str:
    """Pretty-print JSON."""
    return json.dumps(obj, indent=indent, ensure_ascii=False)
