from __future__ import annotations

from typing import Any

import chromadb
import numpy as np
from chromadb.utils import embedding_functions
from sentence_transformers import CrossEncoder

from src.config import config
from src.logger import logger


class VectorStoreError(Exception):
    pass


class VectorStore:
    def __init__(self) -> None:
        self._collection: chromadb.Collection | None = None
        self._embedding_fn: embedding_functions.SentenceTransformerEmbeddingFunction | None = None
        self._reranker: CrossEncoder | None = None
        self._chroma_client: chromadb.PersistentClient | None = None

    def _lazy_init(self) -> chromadb.Collection:
        if self._collection is None:
            logger.info("Initializing ChromaDB at %s with model %s", config.chroma_db_path, config.embedding_model)
            self._chroma_client = chromadb.PersistentClient(path=config.chroma_db_path)
            self._embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=config.embedding_model,
            )
            self._reranker = CrossEncoder(config.embedding_model)
            self._collection = self._chroma_client.get_or_create_collection(
                name="adventureworks_schema",
                embedding_function=self._embedding_fn,
            )
        return self._collection

    def _get_reranker(self) -> CrossEncoder:
        self._lazy_init()
        assert self._reranker is not None
        return self._reranker

    def _expand_query(self, query: str) -> list[str]:
        queries = [query]
        keywords = query.lower().split()
        if len(keywords) > 2:
            queries.append(" ".join(keywords))
        domain_keywords: dict[str, str] = {
            "employee": "employee department headcount hire human resources staff worker",
            "product": "product inventory stock manufacturing sell item goods",
            "customer": "customer client buyer consumer person contact",
            "order": "order sales purchase transaction revenue",
            "vendor": "vendor supplier purchase procurement",
            "department": "department group team section",
            "salary": "salary pay rate wage compensation",
            "leave": "leave vacation absence holiday time off",
        }
        for keyword, expansion in domain_keywords.items():
            if keyword in query.lower():
                queries.append(expansion)
                break
        return queries[: config.query_expansion_count]

    def query(
        self,
        query_text: str,
        top_k: int | None = None,
    ) -> tuple[list[str], list[str], list[float]]:
        collection = self._lazy_init()
        top_k = top_k or config.retrieval_top_k

        expanded_queries = self._expand_query(query_text)

        all_ids: list[str] = []
        all_docs: list[str] = []
        all_distances: list[float] = []

        for eq in expanded_queries:
            try:
                results = collection.query(
                    query_texts=[eq],
                    n_results=top_k * 2,
                    include=["documents", "distances"],
                )
                all_ids.extend(results["ids"][0])
                all_docs.extend(results["documents"][0])
                all_distances.extend(results["distances"][0] if results.get("distances") else [0.0] * len(results["ids"][0]))
            except Exception as e:
                logger.warning("Query expansion search failed for '%s': %s", eq, e)

        if not all_ids:
            return [], [], []

        unique_map: dict[str, tuple[str, float]] = {}
        for doc_id, doc, dist in zip(all_ids, all_docs, all_distances):
            if doc_id not in unique_map or dist < unique_map[doc_id][1]:
                unique_map[doc_id] = (doc, dist)

        merged_ids = list(unique_map.keys())
        merged_docs = [unique_map[i][0] for i in merged_ids]
        merged_distances = [unique_map[i][1] for i in merged_ids]

        reranker = self._get_reranker()
        pairs = [(query_text, doc) for doc in merged_docs]
        if pairs:
            rerank_scores = reranker.predict(pairs)
            ranked_indices = np.argsort(rerank_scores)[::-1][:top_k]
            final_ids = [merged_ids[i] for i in ranked_indices]
            final_docs = [merged_docs[i] for i in ranked_indices]
            final_distances = [merged_distances[i] for i in ranked_indices]
        else:
            final_ids = merged_ids[:top_k]
            final_docs = merged_docs[:top_k]
            final_distances = merged_distances[:top_k]

        return final_ids, final_docs, final_distances

    def get_documents_by_ids(self, ids: list[str]) -> list[str]:
        collection = self._lazy_init()
        try:
            results = collection.get(ids=ids)
            return results["documents"] if results and results["documents"] else []
        except Exception as e:
            logger.warning("Failed to get documents by ids: %s", e)
            return []

    def get_all_table_ids(self) -> list[str]:
        collection = self._lazy_init()
        try:
            all_ids = collection.get(include=[])["ids"]
            table_ids = [i for i in all_ids if i.startswith("table::")]
            return table_ids
        except Exception as e:
            logger.warning("Failed to get all table ids: %s", e)
            return []


vector_store = VectorStore()
