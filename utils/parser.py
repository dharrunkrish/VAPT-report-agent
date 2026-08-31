import json
import re
from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel, ValidationError

from config.settings import get_logger

logger = get_logger("parser")

T = TypeVar("T", bound=BaseModel)


def _strip_markdown_fences(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def parse_json_text(raw: str) -> Dict[str, Any]:
    """Parse JSON from LLM output, tolerating markdown fences and minor formatting issues."""
    text = _strip_markdown_fences(raw)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            from json_repair import repair_json

            data = json.loads(repair_json(text))
        except Exception as exc:
            raise ValueError(f"Could not parse JSON from model output: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("Expected a JSON object at the top level.")
    return data


def extract_task_raw(task) -> str:
    if not task.output:
        raise ValueError("Task produced no output.")
    if task.output.raw:
        raw = str(task.output.raw)
        logger.debug("Task raw output (raw): %s", raw[:1000])
        return raw
    if task.output.json_dict:
        raw = json.dumps(task.output.json_dict)
        logger.debug("Task raw output (json_dict): %s", raw[:1000])
        return raw
    if task.output.pydantic is not None:
        raw = task.output.pydantic.model_dump_json()
        logger.debug("Task raw output (pydantic): %s", raw[:1000])
        return raw
    raise ValueError("Task output was empty.")


def parse_task_output(task, model: Type[T]) -> T:
    """Validate task output against a Pydantic model."""
    agent_role = getattr(getattr(task, "agent", None), "role", None)
    task_desc = getattr(task, "description", "<no description>")
    structured_hint = getattr(task, "expected_output", None) is not None

    logger.info("Parsing output for task; agent=%s structured_hint=%s desc=" + task_desc[:80], agent_role, structured_hint)

    if task.output and task.output.pydantic is not None:
        try:
            return model.model_validate(task.output.pydantic.model_dump())
        except ValidationError as exc:
            logger.exception("Pydantic output failed validation for %s: %s", model.__name__, exc)
            raise ValueError(f"Pydantic output failed validation for {model.__name__}: {exc}") from exc

    if task.output and task.output.json_dict:
        try:
            return model.model_validate(task.output.json_dict)
        except ValidationError as exc:
            logger.exception("JSON dict output failed validation for %s: %s", model.__name__, exc)
            raise ValueError(f"JSON dict output failed validation for {model.__name__}: {exc}") from exc

    raw = extract_task_raw(task)
    logger.info("Raw LLM response (first 2000 chars): %s", raw[:2000])
    try:
        data = parse_json_text(raw)
    except Exception as exc:
        logger.exception("Failed to parse JSON from raw output: %s", exc)
        raise

    try:
        return model.model_validate(data)
    except ValidationError as exc:
        logger.exception("Output failed validation for %s: %s", model.__name__, exc)
        raise ValueError(f"Output failed validation for {model.__name__}: {exc}") from exc
