"""Client RAG-Anything partagé par les scripts CLI et le serveur MCP."""

from __future__ import annotations

import json
from functools import partial
from pathlib import Path
from typing import Any

from lightrag import QueryParam
from lightrag.llm.openai import openai_complete_if_cache, openai_embed
from lightrag.utils import EmbeddingFunc
from raganything import RAGAnything, RAGAnythingConfig

from scripts.config import Settings, load_settings


class RAGClient:
    def __init__(self, project_root: Path | None = None) -> None:
        self.settings = load_settings(project_root)
        self._rag: RAGAnything | None = None

    def _build_rag(self) -> RAGAnything:
        vllm = self.settings.vllm
        rag_cfg = self.settings.rag

        config = RAGAnythingConfig(
            working_dir=str(self.settings.resolve_path(rag_cfg["working_dir"])),
            parser=rag_cfg.get("parser", "mineru"),
            parse_method=rag_cfg.get("parse_method", "auto"),
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )

        llm_model = vllm["llm_model"]
        vision_model = vllm.get("vision_model", llm_model)
        api_key = vllm.get("api_key", "EMPTY")
        base_url = vllm["base_url"]
        embedding_base_url = vllm.get("embedding_base_url", base_url)

        def llm_model_func(
            prompt: str,
            system_prompt: str | None = None,
            history_messages: list | None = None,
            **kwargs: Any,
        ) -> str:
            return openai_complete_if_cache(
                llm_model,
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages or [],
                api_key=api_key,
                base_url=base_url,
                **kwargs,
            )

        def vision_model_func(
            prompt: str,
            system_prompt: str | None = None,
            history_messages: list | None = None,
            image_data: str | None = None,
            messages: list | None = None,
            **kwargs: Any,
        ) -> str:
            if messages:
                return openai_complete_if_cache(
                    vision_model,
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=messages,
                    api_key=api_key,
                    base_url=base_url,
                    **kwargs,
                )

            if image_data:
                user_messages: list[dict[str, Any]] = []
                if system_prompt:
                    user_messages.append({"role": "system", "content": system_prompt})
                user_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                },
                            },
                        ],
                    }
                )
                return openai_complete_if_cache(
                    vision_model,
                    "",
                    system_prompt=None,
                    history_messages=[],
                    messages=user_messages,
                    api_key=api_key,
                    base_url=base_url,
                    **kwargs,
                )

            return llm_model_func(
                prompt,
                system_prompt=system_prompt,
                history_messages=history_messages,
                **kwargs,
            )

        embedding_func = EmbeddingFunc(
            embedding_dim=int(vllm["embedding_dim"]),
            max_token_size=8192,
            func=partial(
                openai_embed.func,
                model=vllm["embedding_model"],
                api_key=api_key,
                base_url=embedding_base_url,
            ),
        )

        return RAGAnything(
            config=config,
            llm_model_func=llm_model_func,
            vision_model_func=vision_model_func,
            embedding_func=embedding_func,
        )

    @property
    def rag(self) -> RAGAnything:
        if self._rag is None:
            self._rag = self._build_rag()
        return self._rag

    @property
    def manifest_path(self) -> Path:
        working_dir = self.settings.resolve_path(self.settings.rag["working_dir"])
        return working_dir / "index_manifest.json"

    def _load_manifest(self) -> dict[str, float]:
        if not self.manifest_path.exists():
            return {}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _save_manifest(self, manifest: dict[str, float]) -> None:
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def list_reference_pdfs(self) -> list[Path]:
        ref_dir = self.settings.resolve_path(self.settings.paths["reference_dir"])
        ref_dir.mkdir(parents=True, exist_ok=True)
        return sorted(ref_dir.glob("*.pdf"))

    async def index_reference_dir(self, force: bool = False) -> dict[str, Any]:
        pdfs = self.list_reference_pdfs()
        if not pdfs:
            return {
                "indexed": [],
                "skipped": [],
                "message": "Aucun PDF trouvé dans reference/.",
            }

        output_dir = self.settings.resolve_path(self.settings.rag["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        manifest = self._load_manifest()
        indexed: list[str] = []
        skipped: list[str] = []

        for pdf in pdfs:
            pdf_key = str(pdf.resolve())
            mtime = pdf.stat().st_mtime
            if not force and manifest.get(pdf_key) == mtime:
                skipped.append(pdf.name)
                continue

            await self.rag.process_document_complete(
                file_path=str(pdf),
                output_dir=str(output_dir),
                parse_method=self.settings.rag.get("parse_method", "auto"),
                parser=self.settings.rag.get("parser", "mineru"),
            )
            manifest[pdf_key] = mtime
            indexed.append(pdf.name)

        self._save_manifest(manifest)
        return {
            "indexed": indexed,
            "skipped": skipped,
            "message": f"{len(indexed)} PDF indexé(s), {len(skipped)} ignoré(s).",
        }

    async def search(self, query: str, mode: str | None = None) -> str:
        query_mode = mode or self.settings.rag.get("query_mode", "hybrid")
        param = QueryParam(mode=query_mode, only_need_context=True)
        result = await self.rag.lightrag.aquery(query, param=param)
        return result if isinstance(result, str) else str(result)

    def get_index_status(self) -> dict[str, Any]:
        manifest = self._load_manifest()
        pdfs = self.list_reference_pdfs()
        files: list[dict[str, Any]] = []

        for pdf in pdfs:
            pdf_key = str(pdf.resolve())
            indexed_mtime = manifest.get(pdf_key)
            files.append(
                {
                    "name": pdf.name,
                    "indexed": indexed_mtime is not None,
                    "up_to_date": indexed_mtime == pdf.stat().st_mtime
                    if indexed_mtime is not None
                    else False,
                }
            )

        return {
            "reference_dir": str(
                self.settings.resolve_path(self.settings.paths["reference_dir"])
            ),
            "indexed_count": sum(1 for item in files if item["indexed"]),
            "total_pdfs": len(files),
            "files": files,
        }
