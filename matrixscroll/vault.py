"""
Obsidian / Local Markdown Vault Search.

Integrates a personal notes vault with Digital Rain. Reuses the BM25 indexer
from search.py to rank and search notes dynamically.
"""

from __future__ import annotations

import os
from pathlib import Path
import time
from typing import List, Dict, Any

from . import search as S

try:
    from . import workspace_config as wc
except ImportError:
    wc = None  # type: ignore

class VaultSearcher:
    def __init__(self, vault_path: str | Path | None = None):
        if vault_path:
            self.vault_path = Path(vault_path).expanduser().resolve()
        else:
            self.vault_path = None
        self._index: Dict[str, Any] | None = None
        self._last_scan_time = 0.0
        self._last_mtime_sum = 0

    def set_path(self, vault_path: str | Path) -> None:
        self.vault_path = Path(vault_path).expanduser().resolve()
        self.clear_cache()

    def clear_cache(self) -> None:
        self._index = None
        self._last_scan_time = 0.0
        self._last_mtime_sum = 0

    def _get_markdown_files(self) -> List[Path]:
        if not self.vault_path or not self.vault_path.exists() or not self.vault_path.is_dir():
            return []
        
        md_files = []
        count = 0
        for root, dirs, files in os.walk(self.vault_path):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for f in files:
                if f.endswith('.md'):
                    md_files.append(Path(root) / f)
                    count += 1
                    if count >= 1000:
                        break
            if count >= 1000:
                break
        return md_files

    def _get_mtime_sum(self, files: List[Path]) -> int:
        total = 0
        for f in files:
            try:
                total += int(f.stat().st_mtime)
            except OSError:
                pass
        return total

    def _build_vault_index(self) -> None:
        """Scan all markdown files in the vault and build/update the BM25 index."""
        if not self.vault_path or not self.vault_path.exists() or not self.vault_path.is_dir():
            self._index = None
            return

        files = self._get_markdown_files()
        mtime_sum = self._get_mtime_sum(files)

        if self._index and mtime_sum == self._last_mtime_sum:
            return

        chunks: List[S.Chunk] = []
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                rel_path = f.relative_to(self.vault_path)
                title = str(rel_path)
                url = f.as_uri()
                
                file_chunks = S.chunk_markdown(content, url, title)
                for c in file_chunks:
                    c.source_type = "obsidian_vault"
                    chunks.append(c)
            except Exception:
                continue

        if chunks:
            self._index = S.build_index(chunks)
        else:
            self._index = {
                "chunks": [],
                "tokens": [],
                "df": {},
                "avgdl": 0.0,
                "N": 0,
            }
        
        self._last_mtime_sum = mtime_sum
        self._last_scan_time = time.time()

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the vault for query, returning ranked list of chunks."""
        self._build_vault_index()
        if not self._index or self._index.get("N", 0) == 0:
            return []
        
        bm25 = S.BM25(self._index)
        return bm25.search(query, k=k, source_type="obsidian_vault")

# Global singleton
_searcher = VaultSearcher()

def search_vault(query: str, vault_path: str = "", k: int = 5) -> List[Dict[str, Any]]:
    """Helper function to run search with global searcher."""
    if not vault_path and wc is not None:
        resolved = wc.resolve_vault_path()
        if resolved:
            vault_path = str(resolved)
    if vault_path:
        _searcher.set_path(vault_path)
    return _searcher.search(query, k=k)
