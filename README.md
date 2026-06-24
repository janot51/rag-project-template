# rag-project-template

Template RAG pour analyser des données avec un LLM enrichi par une **documentation technique indexée localement** via RAG-Anything.

**Stack :**
- **MCP** (Model Context Protocol) — expose la doc indexée à Cursor et Kilocode
- **RAG-Anything** + **MinerU** — parsing PDF et graphe de connaissances LightRAG
- **vLLM** — LLM local (Qwen3.5 122B) ou cloud (Cursor)

---

## Structure

```
rag-project-template/
├── reference/          # PDF à indexer (doc technique)
├── data/               # Données à analyser (Excel, CSV...)
├── rag_storage/        # Index RAG (généré)
├── output/             # Sorties MinerU (généré)
├── scripts/
│   ├── index.py        # Indexer les PDF
│   ├── query.py        # Tester une recherche
│   ├── rag_client.py   # Client RAG réutilisable
│   ├── verify_install.py
│   ├── setup.ps1       # Install Windows (uv)
│   └── setup.sh        # Install Linux (uv)
├── mcp_server/
│   └── server.py       # Serveur MCP
├── .cursor/mcp.json    # Config MCP Cursor
├── .kilo/
│   ├── kilo.jsonc      # Config Kilocode v7
│   └── rules/          # Règles agent
├── config.yaml         # Configuration RAG
├── .env                # Variables d'environnement
├── .env.example
├── pyproject.toml      # Dépendances (uv)
└── .gitignore
```

---

## Installation

### Prérequis

- **Python 3.12+**
- **uv** (gestion de dépendances)
- **vLLM** en local (GB10) ou accès LLM cloud (Cursor)
- **GPU CUDA** pour MinerU (parsing PDF)

### Windows (Cursor)

**Option 1 : Script PowerShell (recommandé)**

```powershell
cd rag-project-template
.\scripts\setup.ps1
```

**Option 2 : Manuel**

```powershell
cd rag-project-template
uv venv .venv
.\.venv\Scripts\activate
uv pip sync .
Copy-Item .env.example .env
```

### Linux / macOS

**Option 1 : Script Bash (recommandé)**

```bash
cd rag-project-template
./scripts/setup.sh
```

**Option 2 : Manuel**

```bash
cd rag-project-template
uv venv .venv
source .venv/bin/activate
uv pip sync .
cp .env.example .env
```

---

## Configuration

### vLLM / LLM

Créez un `.env` à partir de `.env.example` :

```bash
# vLLM local (GB10 / DGX)
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=EMPTY
LLM_MODEL=Qwen/Qwen3.5-122B-Instruct
VISION_MODEL=Qwen/Qwen3.5-122B-Instruct

# Embeddings (optionnel : second serveur vLLM)
EMBEDDING_BASE_URL=http://localhost:8001/v1
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
EMBEDDING_DIM=4096

# MinerU
MINERU_DEVICE=cuda
```

Adapter les noms de modèles selon ce que renvoie `curl http://localhost:8000/v1/models`.

---

## Utilisation

### 1. Préparer la documentation

Déposez vos PDF dans `reference/`.

### 2. Indexer

```bash
python scripts/index.py              # Indexation incrémentale
python scripts/index.py --force      # Réindexation forcée
```

Comptez plusieurs minutes par PDF complexe (parsing + graphe).

### 3. Tester une recherche

```bash
python scripts/query.py "règles de codification"
```

### 4. Utiliser dans Cursor ou Kilocode

Le serveur MCP expose trois outils :

| Outil | Rôle |
|-------|------|
| `search_reference_docs` | Recherche du contexte pertinent (sans réponse générée) |
| `get_index_status` | Liste des PDF indexés |
| `reindex_reference` | Lance l'indexation |

---

## Dupliquer pour une nouvelle mission

```bash
cp -r rag-project-template mon-projet-norme-X
cd mon-projet-norme-X
rm -rf rag_storage output .env
cp .env.example .env
```

Déposer vos PDF dans `reference/` et données dans `data/`, puis indexer.

---

## Utiliser le RAG dans vos scripts

```python
import asyncio
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from scripts.rag_client import RAGClient

async def main():
    client = RAGClient(ROOT)
    context = await client.search("définition du code XYZ")
    print(context)

asyncio.run(main())
```

---

## Dépannage

| Problème | Piste |
|----------|-------|
| MCP ne démarre pas | Vérifier `python` pointe vers le `.venv` du projet |
| MCP timeout (Kilocode) | `.kilo/kilo.jsonc` → `timeout: 300000` (5 min) |
| Modèle introuvable | `curl localhost:8000/v1/models` et adapter `LLM_MODEL` dans `.env` |
| Timeout LLM | Augmenter `provider.*.options.timeout` dans `.kilo/kilo.jsonc` |
| Erreur embedding | Vérifier `EMBEDDING_BASE_URL` et `EMBEDDING_DIM` |
| PDF mal parsé | `PARSE_METHOD=ocr` dans `.env` |
| Index obsolète | `python scripts/index.py --force` |

---

## Licence

Template MIT — RAG-Anything : [HKUDS/RAG-Anything](https://github.com/HKUDS/RAG-Anything)
