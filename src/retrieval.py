from src.config import config
from src.llm_client import llm_client
from src.logger import logger
from src.vector_store import vector_store
from src.database import db


def _translate_query_with_llm(user_query: str, known_table_ids: list[str]) -> list[str]:
    prompt = (
        "You are a SQL schema router. Available tables:\n"
        f"[{', '.join(sorted(known_table_ids))}]\n\n"
        f"Question: '{user_query}'\n\n"
        "Return ONLY the table names required (including join tables), "
        "comma-separated, nothing else. No explanation, no sentences."
    )
    try:
        response = llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
        )
        raw = response.strip()
        candidates = [t.strip() for t in raw.replace("\n", ",").split(",") if t.strip()]
        logger.debug("LLM table routing returned: %s", candidates)
        return candidates
    except Exception as e:
        logger.warning("LLM table routing failed: %s", e)
        return []


def retrieve_schema_context(user_query: str) -> str:
    ids, docs, distances = vector_store.query(user_query)

    if not ids:
        logger.warning("Vector search returned no results for query")
        return ""

    top_distance = distances[0] if distances else None

    if top_distance is not None and top_distance > config.escalation_distance_threshold:
        logger.info(
            "Low confidence (distance=%.2f > %.2f) — escalating to LLM table routing",
            top_distance, config.escalation_distance_threshold,
        )
        known_ids = vector_store.get_all_table_ids()
        table_names = [i.replace("table::", "", 1) for i in known_ids]
        escalated = _translate_query_with_llm(user_query, table_names)
        if escalated:
            prefixed = [f"table::{t}" for t in escalated]
            missing = [p for p in prefixed if p not in ids]
            if missing:
                extra_docs = vector_store.get_documents_by_ids(missing)
                if extra_docs:
                    ids.extend(missing)
                    docs.extend(extra_docs)

    context_parts = list(docs)
    table_ids = [i.replace("table::", "", 1) for i in ids]

    live_columns = db.get_live_table_columns(table_ids)
    if live_columns:
        context_parts.append(
            "\n\nVERIFIED LIVE COLUMNS (pulled directly from the database schema "
            "right now — this is ground truth; use ONLY these exact column names "
            "for these tables, never invent or assume one):\n" + live_columns
        )

    return "\n".join(context_parts)
