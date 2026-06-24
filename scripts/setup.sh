#!/usr/bin/env bash
# Installation sur DGX Spark GB10 (avec internet) avec uv
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Création du venv avec uv..."
uv venv .venv

echo "==> Activation du venv..."
source .venv/bin/activate

echo "==> Installation des dépendances avec uv..."
uv pip sync .

if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "==> .env créé — vérifiez VLLM_BASE_URL et modèles."
fi

echo "==> Vérification..."
python scripts/verify_install.py

echo ""
echo "Prêt pour Kilocode."
echo "1. Ouvrir rag-project-template-gb10.code-workspace"
echo "2. Configurer .env avec les URLs vLLM"
echo "3. python scripts/index.py"
