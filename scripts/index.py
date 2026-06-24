#!/usr/bin/env python
"""Indexe les PDF du dossier reference/ dans RAG-Anything."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag_client import RAGClient


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Indexer les PDF de reference/ avec RAG-Anything."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Réindexer même si le fichier n'a pas changé.",
    )
    args = parser.parse_args()

    client = RAGClient(PROJECT_ROOT)
    result = await client.index_reference_dir(force=args.force)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
