import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict

from docx import Document

from config.settings import OUTPUT_DIR, get_logger

logger = get_logger("output")


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^\w\-.]", "_", name) or "target"


def _timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def save_markdown(content: str, target: str) -> str:
    safe = sanitize_filename(target)
    filename = f"{safe}_report_{_timestamp()}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as handle:
        handle.write(content)
    logger.info("Markdown report saved: %s", filepath)
    return filepath


def save_findings_json(data: Dict[str, Any], target: str) -> str:
    safe = sanitize_filename(target)
    filename = f"{safe}_findings_{_timestamp()}.json"
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
    logger.info("Findings JSON saved: %s", filepath)
    return filepath


def save_docx(document: Document, target: str, suffix: str = "vapt_report") -> str:
    safe = sanitize_filename(target)
    filename = f"{safe}_{suffix}_{_timestamp()}.docx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    document.save(filepath)
    logger.info("Word report saved: %s", filepath)
    return filepath


def load_findings(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Input file not found: {path}")
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be a top-level object.")
    logger.info("Loaded input: %s", path)
    return data
