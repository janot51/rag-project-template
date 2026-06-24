"""Chargement de la configuration projet (config.yaml + .env)."""

from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

_ENV_MAPPINGS = {
    "VLLM_BASE_URL": ("vllm", "base_url"),
    "VLLM_API_KEY": ("vllm", "api_key"),
    "LLM_MODEL": ("vllm", "llm_model"),
    "VISION_MODEL": ("vllm", "vision_model"),
    "EMBEDDING_BASE_URL": ("vllm", "embedding_base_url"),
    "EMBEDDING_MODEL": ("vllm", "embedding_model"),
    "EMBEDDING_DIM": ("vllm", "embedding_dim"),
    "PARSER": ("rag", "parser"),
    "PARSE_METHOD": ("rag", "parse_method"),
    "MINERU_DEVICE": ("rag", "mineru_device"),
}


def ensure_venv_on_path(root: Path) -> None:
    """Ajoute .venv/Scripts au PATH pour que MinerU soit trouvé par RAG-Anything."""
    scripts_dir = root / ".venv" / "Scripts"
    if not scripts_dir.is_dir():
        bin_dir = root / ".venv" / "bin"
        if bin_dir.is_dir():
            scripts_dir = bin_dir
        else:
            return
    current = os.environ.get("PATH", "")
    scripts = str(scripts_dir.resolve())
    if scripts not in current.split(os.pathsep):
        os.environ["PATH"] = scripts + os.pathsep + current


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "config.yaml").exists():
            return candidate
    raise FileNotFoundError(
        "config.yaml introuvable. Exécutez les commandes depuis la racine du projet."
    )


def _set_nested(config: dict[str, Any], keys: tuple[str, ...], value: Any) -> None:
    node = config
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value


def load_settings(project_root: Path | None = None) -> Settings:
    root = project_root or find_project_root()
    ensure_venv_on_path(root)
    load_dotenv(root / ".env", override=False)

    with (root / "config.yaml").open(encoding="utf-8") as handle:
        config: dict[str, Any] = yaml.safe_load(handle) or {}

    for env_key, path in _ENV_MAPPINGS.items():
        raw = os.getenv(env_key)
        if raw is None or raw == "":
            continue
        value: Any = raw
        if path[-1] == "embedding_dim":
            value = int(raw)
        _set_nested(config, path, value)

    return Settings(root=root, config=config)


class Settings:
    def __init__(self, root: Path, config: dict[str, Any]) -> None:
        self.root = root
        self._config = config

    def resolve_path(self, relative: str) -> Path:
        path = Path(relative)
        if path.is_absolute():
            return path
        return (self.root / path).resolve()

    def __getitem__(self, key: str) -> Any:
        return deepcopy(self._config[key])

    @property
    def vllm(self) -> dict[str, Any]:
        return deepcopy(self._config["vllm"])

    @property
    def rag(self) -> dict[str, Any]:
        return deepcopy(self._config["rag"])

    @property
    def paths(self) -> dict[str, Any]:
        return deepcopy(self._config["paths"])
