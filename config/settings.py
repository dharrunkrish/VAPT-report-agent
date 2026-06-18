import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Project root (parent of config/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

# Reduce CrewAI / OpenTelemetry overhead at import time
os.environ.setdefault("OTEL_SDK_DISABLED", "true")

GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "outputs")
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

SEVERITY_LEVELS = ("Critical", "High", "Medium", "Low", "Informational")

Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
(PROJECT_ROOT / "logs").mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(f"vaptagen.{name}")
    if logger.handlers:
        return logger

    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)

    log_file = PROJECT_ROOT / "logs" / f"{name}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    return logger
