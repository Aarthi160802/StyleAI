"""
logger.py – structured JSON session logger for StyleAI agent runs.
"""
import json
import os
import datetime
from code.config import LOGS_DIR


def _ensure_dir() -> None:
    os.makedirs(LOGS_DIR, exist_ok=True)


def save_session_log(session_data: dict) -> str:
    """Persist the full agent session to a timestamped JSON file.
    Returns the file path."""
    _ensure_dir()
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(LOGS_DIR, f"session_{ts}.json")
    with open(filename, "w", encoding="utf-8") as fh:
        json.dump(session_data, fh, indent=2, ensure_ascii=False)
    return filename


def list_log_files() -> list[str]:
    """Return sorted list of all log file paths (newest first)."""
    _ensure_dir()
    files = [
        os.path.join(LOGS_DIR, f)
        for f in os.listdir(LOGS_DIR)
        if f.endswith(".json")
    ]
    return sorted(files, reverse=True)


def load_log_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)
