#!/usr/bin/env python3
"""VAPTagen — AI-assisted VAPT report generation (CrewAI + Groq + Word)."""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_logger
from crew_orchestrator import generate_and_persist
from utils.output import load_findings

logger = get_logger("main")


def print_banner() -> None:
    print("\n" + "=" * 60)
    print("  VAPTagen — AI VAPT Report Generator")
    print("  CrewAI + Groq | JSON + Word (.docx) + Markdown")
    print("=" * 60 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate enterprise VAPT reports from structured finding JSON."
    )
    parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to input JSON (single finding or findings array).",
    )
    args = parser.parse_args()

    print_banner()

    try:
        input_path = Path(args.input)
        if not input_path.is_absolute():
            input_path = PROJECT_ROOT / input_path

        payload = load_findings(str(input_path))
        target = payload.get("target", "unknown")
        if "finding" in payload:
            count = 1
        elif "findings" in payload:
            count = len(payload.get("findings", []))
        else:
            count = 1

        print(f"  Target:   {target}")
        print(f"  Findings: {count}")
        print(f"  Input:    {input_path}")
        print("\n  Generating report (Word + JSON + Markdown)...\n")

        result = generate_and_persist(payload)

        print("  ✓ Report generation complete\n")
        print(f"  Word:     {result['report_docx_path']}")
        print(f"  JSON:     {result['findings_json_path']}")
        print(f"  Markdown: {result['report_markdown_path']}")
        print("\n" + "=" * 60 + "\n")

        logger.info(
            "Done. docx=%s json=%s md=%s",
            result["report_docx_path"],
            result["findings_json_path"],
            result["report_markdown_path"],
        )
        return 0

    except EnvironmentError as exc:
        logger.error("%s", exc)
        print(f"\n  ERROR: {exc}\n", file=sys.stderr)
        return 2
    except (ValueError, FileNotFoundError) as exc:
        logger.error("%s", exc)
        print(f"\n  ERROR: {exc}\n", file=sys.stderr)
        return 1
    except Exception as exc:
        logger.exception("Report generation failed: %s", exc)
        print(f"\n  ERROR: {exc}\n", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
