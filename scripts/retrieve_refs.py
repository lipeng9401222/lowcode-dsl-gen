#!/usr/bin/env python3
"""retrieve_refs.py — 轻量 references 检索工具.

不是向量 RAG。只用关键词计分帮助 dispatcher/atomic skill 选择应读的 reference。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parent.parent
REFERENCES = SKILL_ROOT / "references"

ASSET_HINTS = {
    "app-shell": ["appinfo", "appref", "directory-structure.md"],
    "codeitem": ["codeitem"],
    "mis": ["mis"],
    "module": ["module"],
    "pagedesigne": ["pagedesigne"],
    "workflow": ["workflow"],
    "event": ["event"],
}


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]{2,}", text)]


def score_file(path: Path, query_terms: list[str], asset: str) -> tuple[int, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0, ""
    lower_path = path.as_posix().lower()
    lower_text = text.lower()
    score = 0
    for term in query_terms:
        score += lower_path.count(term) * 8
        score += lower_text.count(term)
    for hint in ASSET_HINTS.get(asset, []):
        if hint.lower() in lower_path:
            score += 20
    snippet = ""
    for line in text.splitlines():
        line_lower = line.lower()
        if any(term in line_lower for term in query_terms):
            snippet = line.strip()
            break
    return score, snippet


def retrieve(query: str, asset: str = "", limit: int = 5) -> list[tuple[int, Path, str]]:
    terms = tokenize(query + " " + asset)
    if not terms and asset:
        terms = [asset]
    results: list[tuple[int, Path, str]] = []
    for path in REFERENCES.rglob("*.md"):
        score, snippet = score_file(path, terms, asset)
        if score > 0:
            results.append((score, path, snippet))
    results.sort(key=lambda item: (-item[0], item[1].as_posix()))
    return results[:limit]


def cli() -> int:
    parser = argparse.ArgumentParser(description="轻量检索 references 文档")
    parser.add_argument("query", help="检索关键词或自然语言需求")
    parser.add_argument("--asset", choices=sorted(ASSET_HINTS), default="", help="资产类型")
    parser.add_argument("--limit", type=int, default=5, help="返回数量 [5]")
    args = parser.parse_args()
    results = retrieve(args.query, args.asset, args.limit)
    for score, path, snippet in results:
        rel = path.relative_to(SKILL_ROOT)
        print(f"{score}\t{rel}")
        if snippet:
            print(f"  {snippet[:180]}")
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(cli())
