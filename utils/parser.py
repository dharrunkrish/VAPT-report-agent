import json
import re
from typing import Any, Dict, Type, TypeVar

from pydantic import BaseModel, ValidationError

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
        return str(task.output.raw)
    if task.output.json_dict:
        return json.dumps(task.output.json_dict)
    if task.output.pydantic is not None:
        return task.output.pydantic.model_dump_json()
    raise ValueError("Task output was empty.")


def parse_task_output(task, model: Type[T]) -> T:
    """Validate task output against a Pydantic model."""
    if task.output and task.output.pydantic is not None:
        return model.model_validate(task.output.pydantic.model_dump())

    if task.output and task.output.json_dict:
        return model.model_validate(task.output.json_dict)

    raw = extract_task_raw(task)
    try:
        data = parse_json_text(raw)
        return model.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Output failed validation for {model.__name__}: {exc}") from exc
