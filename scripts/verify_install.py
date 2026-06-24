#!/usr/bin/env python
"""Vérifie que l'installation est prête pour Cursor."""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config import ensure_venv_on_path, load_settings
from scripts.rag_client import RAGClient


def main() -> int:
    ensure_venv_on_path(PROJECT_ROOT)
    load_settings(PROJECT_ROOT)

    checks: dict[str, bool | str] = {}

    try:
        from raganything import RAGAnything

        rag = RAGAnything()
        checks["raganything"] = True
        checks["mineru"] = bool(rag.check_parser_installation())
    except Exception as exc:
        checks["raganything"] = str(exc)
        checks["mineru"] = False

    try:
        import mcp  # noqa: F401

        checks["mcp"] = True
    except Exception as exc:
        checks["mcp"] = str(exc)

    client = RAGClient(PROJECT_ROOT)
    checks["index_status"] = client.get_index_status()
    checks["venv_python"] = sys.executable
    checks["ready"] = checks.get("raganything") is True and checks.get("mcp") is True

    print(json.dumps(checks, indent=2, ensure_ascii=False))
    return 0 if checks["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
