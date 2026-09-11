__all__ = [
    "build_vapt_docx",
    "get_llm",
    "load_findings",
    "save_docx",
    "save_findings_json",
    "save_markdown",
    "parse_task_output",
    "render_full_report",
]


def build_vapt_docx(*args, **kwargs):
    from .docx_report import build_vapt_docx as _build_vapt_docx

    return _build_vapt_docx(*args, **kwargs)


def get_llm(*args, **kwargs):
    from .llm import get_llm as _get_llm

    return _get_llm(*args, **kwargs)


def load_findings(*args, **kwargs):
    from .output import load_findings as _load_findings

    return _load_findings(*args, **kwargs)


def save_docx(*args, **kwargs):
    from .output import save_docx as _save_docx

    return _save_docx(*args, **kwargs)


def save_findings_json(*args, **kwargs):
    from .output import save_findings_json as _save_findings_json

    return _save_findings_json(*args, **kwargs)


def save_markdown(*args, **kwargs):
    from .output import save_markdown as _save_markdown

    return _save_markdown(*args, **kwargs)


def parse_task_output(*args, **kwargs):
    from .parser import parse_task_output as _parse_task_output

    return _parse_task_output(*args, **kwargs)


def render_full_report(*args, **kwargs):
    from .render import render_full_report as _render_full_report

    return _render_full_report(*args, **kwargs)
