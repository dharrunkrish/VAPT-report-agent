from typing import Optional

from utils.schemas import ReportSection

_MANUAL_VERIFICATION = "Requires manual verification"


def _normalize_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    lowered = normalized.lower()
    if lowered in {"n/a", "na", "none", "unknown", "not provided", "requires manual verification"}:
        return _MANUAL_VERIFICATION
    return value


def normalize_report_section(section: ReportSection) -> ReportSection:
    """Guard against unsupported automation guesses in mapping fields."""
    updates: dict[str, object] = {}

    if not section.severity or section.severity.strip().lower() in {"n/a", "na", "unknown", "none"}:
        updates["severity"] = _MANUAL_VERIFICATION

    if not section.cwe or _normalize_optional_text(section.cwe) is None:
        updates["cwe"] = _MANUAL_VERIFICATION
    elif section.cwe.strip().lower() in {"n/a", "na", "unknown", "none", "requires manual verification"}:
        updates["cwe"] = _MANUAL_VERIFICATION

    if not section.owasp or _normalize_optional_text(section.owasp) is None:
        updates["owasp"] = _MANUAL_VERIFICATION
    elif section.owasp.strip().lower() in {"n/a", "na", "unknown", "none", "requires manual verification"}:
        updates["owasp"] = _MANUAL_VERIFICATION

    if not section.wstg or _normalize_optional_text(section.wstg) is None:
        updates["wstg"] = _MANUAL_VERIFICATION
    elif section.wstg.strip().lower() in {"n/a", "na", "unknown", "none", "requires manual verification"}:
        updates["wstg"] = _MANUAL_VERIFICATION

    if not updates:
        return section
    return section.model_copy(update=updates)
