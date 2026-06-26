"""
Lightweight, dependency-free retrieval over the scraped Cursor docs.

Implements a small BM25 ranker in pure Python so the bot can find the most
relevant documentation chunks for a question with no external services
(no vector DB, no embedding model required).
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any

# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Very small stopword list - just the noise words that hurt ranking.
_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in",
    "on", "for", "is", "are", "be", "with", "as", "by", "at", "this", "that",
    "it", "you", "your", "i", "we", "can", "do", "does", "how", "what", "when",
    "where", "which", "from", "into", "about",
}


def tokenize(text: str) -> List[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


# ---------------------------------------------------------------------------
# Chunking - split markdown into heading-scoped passages
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    doc_title: str
    url: str
    heading: str
    text: str
    # Extra fields let one index hold two content types:
    #   source_type="cursor_doc"  -> scraped Cursor documentation (default)
    #   source_type="mcp_catalog" -> an MCP server / skill catalog entry
    # All default so an older index.json (without these keys) still loads.
    source_type: str = "cursor_doc"
    name: str = ""            # catalog: the MCP server name
    tags: str = ""            # catalog: space/comma separated tags
    github_url: str = ""      # catalog: source repo
    install_snippet: str = ""  # catalog: ready-to-paste mcp.json fragment

    def display_text(self) -> str:
        head = f"{self.doc_title} — {self.heading}" if self.heading else self.doc_title
        return f"## {head}\n{self.text}".strip()


def _doc_title(md: str, fallback: str) -> str:
    for line in md.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def chunk_markdown(md: str, url: str, fallback_title: str,
                   max_chars: int = 1400) -> List[Chunk]:
    """Split a markdown document into chunks scoped by H2 (## ) sections."""
    title = _doc_title(md, fallback_title)
    chunks: List[Chunk] = []

    # Split on H2 headings while keeping the heading text.
    parts = re.split(r"\n(?=## )", md)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        lines = part.splitlines()
        heading = ""
        if lines and lines[0].startswith("## "):
            heading = lines[0][3:].strip()
            body = "\n".join(lines[1:]).strip()
        elif lines and lines[0].startswith("# "):
            body = "\n".join(lines[1:]).strip()
        else:
            body = part

        # Drop the boilerplate sitemap footer.
        body = re.sub(r"\n---\s*\n## Sitemap[\s\S]*$", "", body).strip()
        if not body:
            continue

        # Further split overly long sections on paragraph boundaries.
        if len(body) <= max_chars:
            chunks.append(Chunk(title, url, heading, body))
        else:
            buf = ""
            for para in body.split("\n\n"):
                if len(buf) + len(para) + 2 > max_chars and buf:
                    chunks.append(Chunk(title, url, heading, buf.strip()))
                    buf = para
                else:
                    buf = f"{buf}\n\n{para}" if buf else para
            if buf.strip():
                chunks.append(Chunk(title, url, heading, buf.strip()))

    return chunks


# ---------------------------------------------------------------------------
# Index build / load
# ---------------------------------------------------------------------------

def build_index(chunks: List[Chunk]) -> Dict[str, Any]:
    docs_tokens = [
        tokenize(" ".join((c.text, c.heading, c.doc_title, c.name, c.tags)))
        for c in chunks
    ]
    df: Dict[str, int] = {}
    for toks in docs_tokens:
        for term in set(toks):
            df[term] = df.get(term, 0) + 1
    lengths = [len(t) for t in docs_tokens]
    avgdl = (sum(lengths) / len(lengths)) if lengths else 0.0
    return {
        "chunks": [asdict(c) for c in chunks],
        "tokens": docs_tokens,
        "df": df,
        "avgdl": avgdl,
        "N": len(chunks),
    }


def save_index(index: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index), encoding="utf-8")


def load_index(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# BM25 search
# ---------------------------------------------------------------------------

class BM25:
    def __init__(self, index: Dict[str, Any], k1: float = 1.5, b: float = 0.75):
        self.chunks = index["chunks"]
        self.tokens = index["tokens"]
        self.df = index["df"]
        self.avgdl = index["avgdl"] or 1.0
        self.N = index["N"] or 1
        self.k1 = k1
        self.b = b
        # The index is immutable after load, so precompute per-document term
        # frequencies and lengths once instead of rebuilding them on every query.
        self.doc_len = [len(doc) for doc in self.tokens]
        self.doc_tf: List[Dict[str, int]] = []
        for doc in self.tokens:
            tf: Dict[str, int] = {}
            for t in doc:
                tf[t] = tf.get(t, 0) + 1
            self.doc_tf.append(tf)
        self._idf_cache: Dict[str, float] = {}

    def _idf(self, term: str) -> float:
        cached = self._idf_cache.get(term)
        if cached is not None:
            return cached
        n = self.df.get(term, 0)
        value = math.log(1 + (self.N - n + 0.5) / (n + 0.5))
        self._idf_cache[term] = value
        return value

    def search(self, query: str, k: int = 5,
               source_type: str | None = None) -> List[Dict[str, Any]]:
        """Rank chunks for `query`.

        If `source_type` is given (e.g. "cursor_doc" or "mcp_catalog"), only
        chunks of that type are considered. Chunks from an older index that
        predate the field default to "cursor_doc".
        """
        q_terms = tokenize(query)
        if not q_terms:
            return []
        scores = []
        for i, tf in enumerate(self.doc_tf):
            if not tf:
                scores.append(0.0)
                continue
            if source_type is not None and \
                    self.chunks[i].get("source_type", "cursor_doc") != source_type:
                scores.append(0.0)
                continue
            dl = self.doc_len[i]
            score = 0.0
            for term in q_terms:
                freq = tf.get(term)
                if not freq:
                    continue
                denom = freq + self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                score += self._idf(term) * (freq * (self.k1 + 1)) / denom
            scores.append(score)

        ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for i in ranked[:k]:
            if scores[i] <= 0:
                break
            c = self.chunks[i]
            results.append({**c, "score": round(scores[i], 3)})
        return results
