#!/usr/bin/env python
"""Serveur MCP local — expose la doc de référence indexée à Cursor et Kilocode."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.config import ensure_venv_on_path
from scripts.rag_client import RAGClient

ensure_venv_on_path(PROJECT_ROOT)

server = Server("rag-reference")
_client: RAGClient | None = None


def get_client() -> RAGClient:
    global _client
    if _client is None:
        _client = RAGClient(PROJECT_ROOT)
    return _client


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search_reference_docs",
            description=(
                "Recherche du contexte pertinent dans la documentation technique "
                "indexée (PDF dans reference/). Retourne des extraits, tableaux "
                "et relations du graphe de connaissances — sans générer de réponse."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question ou mots-clés métier.",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["local", "global", "hybrid", "naive", "mix"],
                        "description": "Mode LightRAG (défaut: hybrid).",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_index_status",
            description=(
                "Liste les PDF de reference/ et indique s'ils sont indexés "
                "dans RAG-Anything."
            ),
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="reindex_reference",
            description=(
                "Indexe ou réindexe les PDF du dossier reference/. "
                "Peut prendre plusieurs minutes."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "force": {
                        "type": "boolean",
                        "description": "Réindexer même si inchangé.",
                        "default": False,
                    }
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    client = get_client()

    if name == "search_reference_docs":
        query = arguments.get("query", "").strip()
        if not query:
            return [TextContent(type="text", text="Erreur: query vide.")]
        context = await client.search(query, mode=arguments.get("mode"))
        return [TextContent(type="text", text=context)]

    if name == "get_index_status":
        status = client.get_index_status()
        return [
            TextContent(
                type="text",
                text=json.dumps(status, indent=2, ensure_ascii=False),
            )
        ]

    if name == "reindex_reference":
        result = await client.index_reference_dir(force=bool(arguments.get("force")))
        return [
            TextContent(
                type="text",
                text=json.dumps(result, indent=2, ensure_ascii=False),
            )
        ]

    return [TextContent(type="text", text=f"Outil inconnu: {name}")]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
