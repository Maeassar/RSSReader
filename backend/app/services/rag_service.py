"""
RAG (Retrieval-Augmented Generation) service.

Embedding: SiliconFlow BAAI/bge-m3 (1024-dim, OpenAI-compatible)
Vector store: sqlite-vec (SQLite extension)
Generation: shared AI Provider config (OpenAI-compatible)

Configuration — set these environment variables or fill in directly:
  SILICONFLOW_API_KEY: SiliconFlow API key for embeddings
  OPENAI_API_KEY     : shared chat provider API key
  OPENAI_BASE_URL    : shared chat provider base URL
  OPENAI_MODEL       : shared chat provider model
"""

from __future__ import annotations

import os
import sqlite3
import struct

import sqlite_vec
from openai import OpenAI

from app.database import DB_PATH, get_connection
from app.repositories import repository
from app.services.secret_store import decrypt_secret

# ── Configuration ────────────────────────────────────────────────────────────

# Defaults from environment variables; overridden at runtime by DB values via get_config()
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
EMBEDDING_MODEL = "BAAI/bge-m3"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-flash"

EMBEDDING_DIM = 1024  # BAAI/bge-m3 output dimension
TOP_K = 5             # number of chunks to retrieve


def get_config() -> dict:
    """Read RAG config from DB, fall back to env vars."""
    defaults = {
        "rag_siliconflow_api_key": os.environ.get("SILICONFLOW_API_KEY", ""),
        "rag_siliconflow_base_url": SILICONFLOW_BASE_URL,
        "rag_embedding_model": EMBEDDING_MODEL,
        "rag_embedding_dim": str(EMBEDDING_DIM),
        "rag_deepseek_api_key": os.environ.get("DEEPSEEK_API_KEY", ""),
        "rag_deepseek_base_url": DEEPSEEK_BASE_URL,
        "rag_deepseek_model": DEEPSEEK_MODEL,
    }
    try:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT key, value FROM app_config WHERE key LIKE 'rag_%'"
            ).fetchall()
        for row in rows:
            if row["value"]:
                defaults[row["key"]] = row["value"]
    except Exception:
        pass
    defaults["rag_siliconflow_api_key"] = decrypt_secret(defaults.get("rag_siliconflow_api_key", ""))
    defaults["rag_deepseek_api_key"] = decrypt_secret(defaults.get("rag_deepseek_api_key", ""))
    return defaults


def get_chat_provider_config() -> dict:
    """Return the default LLM Provider used by RAG chat generation."""
    try:
        provider = repository.get_default_llm_provider()
        if provider.get("base_url") and provider.get("model"):
            return provider
    except ValueError:
        pass

    cfg = get_config()
    return {
        "name": "Legacy RAG Chat",
        "base_url": cfg.get("rag_deepseek_base_url", DEEPSEEK_BASE_URL),
        "api_key": cfg.get("rag_deepseek_api_key", ""),
        "model": cfg.get("rag_deepseek_model", DEEPSEEK_MODEL),
        "enabled": True,
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _vec_conn() -> sqlite3.Connection:
    """Return a connection with sqlite-vec loaded."""
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def _serialize(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def _embed(text: str) -> list[float]:
    cfg = get_config()
    dim = int(cfg.get("rag_embedding_dim", EMBEDDING_DIM))
    client = OpenAI(api_key=cfg["rag_siliconflow_api_key"], base_url=cfg["rag_siliconflow_base_url"])
    resp = client.embeddings.create(
        model=cfg["rag_embedding_model"],
        input=text,
        dimensions=dim,
    )
    vec = resp.data[0].embedding
    if len(vec) != dim:
        raise ValueError(
            f"Embedding 维度不匹配：模型返回 {len(vec)} 维，但向量索引固定为 {dim} 维。"
            f"请使用输出 {dim} 维的 Embedding 模型，或在 AI 设置中修改向量维度后重新建立索引。"
        )
    return vec


# ── Vector table init ─────────────────────────────────────────────────────────

def _get_current_vec_dim(conn: sqlite3.Connection) -> int | None:
    """Return the dimension of the existing entries_vec table, or None if it doesn't exist."""
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='entries_vec'"
    ).fetchone()
    if row is None:
        return None
    import re
    m = re.search(r'FLOAT\[(\d+)\]', row[0] or "")
    return int(m.group(1)) if m else None


def initialize_vec_table() -> None:
    """Create the vec0 virtual table if needed, recreating it if the dimension changed."""
    cfg = get_config()
    dim = int(cfg.get("rag_embedding_dim", EMBEDDING_DIM))
    with _vec_conn() as conn:
        existing_dim = _get_current_vec_dim(conn)
        if existing_dim is not None and existing_dim != dim:
            # dimension changed — drop and recreate (data must be re-indexed)
            conn.execute("DROP TABLE entries_vec")
            existing_dim = None
        if existing_dim is None:
            conn.execute(
                f"CREATE VIRTUAL TABLE entries_vec "
                f"USING vec0(entry_id INTEGER PRIMARY KEY, embedding FLOAT[{dim}])"
            )


# ── Indexing ──────────────────────────────────────────────────────────────────

def _text_for_entry(entry_id: int) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT title, summary, cleaned_markdown FROM entries WHERE id = ?",
            (entry_id,),
        ).fetchone()
    if row is None:
        return ""
    parts = [row["title"] or "", row["summary"] or "", (row["cleaned_markdown"] or "")[:2000]]
    return "\n".join(p for p in parts if p)


def index_entry(entry_id: int) -> None:
    """Embed a single entry and upsert into the vector table."""
    text = _text_for_entry(entry_id)
    if not text.strip():
        return
    vec = _embed(text)
    with _vec_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO entries_vec(entry_id, embedding) VALUES (?, ?)",
            (entry_id, _serialize(vec)),
        )


def index_all_entries() -> dict:
    """Embed all entries not yet in the vector table, and remove stale vectors.
    Returns {"added": n, "removed": n}."""
    with get_connection() as conn:
        rows = conn.execute("SELECT id FROM entries").fetchall()
    live_ids = {r["id"] for r in rows}

    with _vec_conn() as conn:
        vec_ids = {r[0] for r in conn.execute("SELECT entry_id FROM entries_vec").fetchall()}

    # add missing
    pending = [eid for eid in live_ids if eid not in vec_ids]
    added = 0
    for entry_id in pending:
        try:
            index_entry(entry_id)
            added += 1
        except Exception:
            pass

    # remove stale (vectors for deleted entries)
    stale = vec_ids - live_ids
    removed = 0
    if stale:
        with _vec_conn() as conn:
            for entry_id in stale:
                try:
                    conn.execute("DELETE FROM entries_vec WHERE entry_id = ?", (entry_id,))
                    removed += 1
                except Exception:
                    pass

    return {"added": added, "removed": removed}


def delete_entry_vec(entry_id: int) -> None:
    """Remove a single entry from the vector table."""
    try:
        with _vec_conn() as conn:
            conn.execute("DELETE FROM entries_vec WHERE entry_id = ?", (entry_id,))
    except Exception:
        pass


# ── Retrieval ─────────────────────────────────────────────────────────────────

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Return top-k articles most similar to the query."""
    q_vec = _embed(query)
    # fetch extra candidates to account for deleted entries that may no longer exist
    fetch_k = top_k * 3
    with _vec_conn() as conn:
        rows = conn.execute(
            """
            SELECT entry_id, distance
            FROM entries_vec
            WHERE embedding MATCH ?
              AND k = ?
            ORDER BY distance
            """,
            (_serialize(q_vec), fetch_k),
        ).fetchall()
    if not rows:
        return []
    entry_ids = [r["entry_id"] for r in rows]
    distance_map = {r["entry_id"]: r["distance"] for r in rows}
    placeholders = ",".join("?" * len(entry_ids))
    with get_connection() as conn:
        entries = conn.execute(
            f"""
            SELECT entries.id, entries.title, entries.link, entries.summary,
                   entries.cleaned_markdown, entries.published_at,
                   feeds.title AS feed_title
            FROM entries
            JOIN feeds ON feeds.id = entries.feed_id
            WHERE entries.id IN ({placeholders})
            """,
            entry_ids,
        ).fetchall()
    result = []
    for e in entries:
        result.append({
            "id": e["id"],
            "title": e["title"],
            "url": e["link"] or "",
            "feed_title": e["feed_title"],
            "published_at": e["published_at"],
            "summary": e["summary"],
            "snippet": (e["cleaned_markdown"] or e["summary"] or "")[:500],
            "distance": distance_map.get(e["id"], 9999),
        })
    result.sort(key=lambda x: x["distance"])
    return result[:top_k]


# ── Generation ────────────────────────────────────────────────────────────────

def ask(question: str) -> dict:
    """Full RAG pipeline: retrieve relevant articles then generate an answer."""
    sources = retrieve(question)
    if not sources:
        return {
            "answer": "暂时没有找到相关文章，请先同步订阅源或等待向量索引完成。",
            "sources": [],
        }

    context_parts = []
    for i, s in enumerate(sources, 1):
        context_parts.append(
            f"[{i}] 标题：{s['title']}\n来源：{s['feed_title']}\n内容片段：{s['snippet']}"
        )
    context = "\n\n".join(context_parts)

    system_prompt = (
        "你是一个 RSS 阅读助手。根据下面提供的文章片段回答用户问题。"
        "回答要简洁、准确，并在末尾用 [1][2] 等编号标注引用来源。"
        "如果文章片段中没有足够信息，请如实说明。"
    )
    user_prompt = f"以下是检索到的相关文章：\n\n{context}\n\n用户问题：{question}"

    provider = get_chat_provider_config()
    if not provider.get("enabled", True):
        raise ValueError("AI Provider 未启用，请先在 AI 设置中启用通用 Provider。")
    if not provider.get("base_url") or not provider.get("model"):
        raise ValueError("AI Provider 缺少 Base URL 或模型名称，请先在 AI 设置中配置。")

    client = OpenAI(api_key=provider.get("api_key") or "EMPTY", base_url=provider["base_url"])
    resp = client.chat.completions.create(
        model=provider["model"],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1024,
    )
    answer = resp.choices[0].message.content or ""

    return {"answer": answer, "sources": sources}
