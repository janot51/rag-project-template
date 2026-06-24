# Agent — rag-project-template

Ce projet analyse des données (`data/`) avec un LLM enrichi par une **documentation technique indexée localement** (`reference/`) via RAG-Anything.

## Documentation technique (RAG local)

Avant toute réponse métier :

1. Interroger le serveur MCP **`rag-reference`** avec `search_reference_docs`.
2. Si la recherche est vide, vérifier l'index avec `get_index_status`.
3. Ne pas deviner les règles techniques — appliquer le contexte RAG retourné.
4. `data/` = données à traiter ; `reference/` = doc indexée.
5. Proposer `reindex_reference` seulement si des PDF ont changé dans `reference/`.

## Stack

- **Cursor** (Windows) : LLM cloud + `.cursor/mcp.json`
- **VSCode + Kilocode v7** (GB10) : vLLM local + `.kilo/kilo.jsonc`
- **vLLM** : `http://localhost:8000/v1` (LLM), `http://localhost:8001/v1` (embeddings)
