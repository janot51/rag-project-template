#!/usr/bin/env python
"""Interroge le RAG en CLI et affiche le contexte récupéré."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.rag_client import RAGClient


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rechercher du contexte dans la doc de référence indexée."
    )
    parser.add_argument("query", help="Question ou mots-clés de recherche.")
    parser.add_argument(
        "--mode",
        default=None,
        choices=["local", "global", "hybrid", "naive", "mix"],
        help="Mode de recherche LightRAG (défaut: config.yaml).",
    )
    args = parser.parse_args()

    client = RAGClient(PROJECT_ROOT)
    context = await client.search(args.query, mode=args.mode)
    print(context)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
