import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from sentence_transformers import CrossEncoder, SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

from src.logger import logger


EVAL_SUITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "eval_suite.json")
CHROMA_DB_PATH = os.environ.get("CHROMA_DB_PATH", "./chroma_db")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "BAAI/bge-base-en-v1.5")
COLLECTION_NAME = "adventureworks_schema"


def normalize_id(raw_id: str) -> str:
    for prefix in ("table::", "yaml::", "rule::", "view::"):
        if raw_id.startswith(prefix):
            return raw_id[len(prefix):]
    return raw_id


def is_table_id(raw_id: str) -> bool:
    if raw_id.startswith("rule::") or raw_id.startswith("view::") or raw_id.startswith("yaml::"):
        return False
    normalized = normalize_id(raw_id)
    if "." not in normalized:
        return False
    known_schemas = ("Sales.", "Production.", "Purchasing.", "HumanResources.", "Person.", "dbo.")
    return any(normalized.startswith(s) for s in known_schemas)


def expand_query(query: str) -> list[str]:
    queries = [query]
    keywords = query.lower().split()
    if len(keywords) > 2:
        queries.append(" ".join(keywords))
    domain_map = {
        "employee": "employee department headcount hire human resources staff worker",
        "product": "product inventory stock manufacturing sell item goods available sale catalog",
        "customer": "customer client buyer consumer person contact",
        "order": "order sales purchase transaction revenue",
        "vendor": "vendor supplier purchase procurement supply",
        "department": "department group team section organizational",
        "salary": "salary pay rate wage compensation",
        "leave": "leave vacation absence holiday time off",
        "bike": "bike bicycle mountain road touring product category",
        "address": "address shipping billing location city state country",
    }
    for keyword, expansion in domain_map.items():
        if keyword in query.lower():
            queries.append(expansion)
            break
    return queries


def run_evals(top_k: int = 15) -> None:
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    collection = client.get_collection(COLLECTION_NAME)
    encoder = SentenceTransformer(EMBEDDING_MODEL)
    reranker = CrossEncoder(EMBEDDING_MODEL)

    with open(EVAL_SUITE_PATH, "r") as f:
        suite = json.load(f)

    results = []
    passed = 0

    for test in suite:
        query = test["query"]
        expected = set(test["expected_tables"])

        expanded_queries = expand_query(query)
        all_ids: list[str] = []

        for eq in expanded_queries:
            embedding = encoder.encode(eq).tolist()
            hits = collection.query(query_embeddings=[embedding], n_results=top_k * 2)
            all_ids.extend(hits["ids"][0])

        unique_ids = list(dict.fromkeys(all_ids))
        table_ids = [uid for uid in unique_ids if is_table_id(uid)]
        normalized = [normalize_id(uid) for uid in table_ids]
        retrieved = set(normalized)

        if len(normalized) > top_k:
            table_docs = collection.get(ids=[i for i in unique_ids if is_table_id(i)])
            if table_docs and table_docs["documents"]:
                pairs = [[query, doc] for doc in table_docs["documents"]]
                scores = reranker.predict(pairs)
                scored = list(zip(normalized, scores))
                scored.sort(key=lambda x: x[1], reverse=True)
                retrieved = set(n for n, _ in scored[:top_k])

        hit = expected.issubset(retrieved)
        if hit:
            passed += 1

        results.append({
            "query": query,
            "expected": list(expected),
            "retrieved": list(retrieved),
            "passed": hit,
            "missed": list(expected - retrieved),
        })

    score = (passed / len(suite)) * 100
    logger.info("Eval Score: %.1f%% (%d/%d passed)", score, passed, len(suite))

    report_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "eval_report.json")
    with open(report_path, "w") as f:
        json.dump({"score": score, "results": results}, f, indent=2)
    logger.info("Report written to %s", report_path)

    print(f"\nEval Score: {score:.1f}% ({passed}/{len(suite)} passed)")
    print("\n=== FAILED TESTS ===")
    for r in results:
        if not r["passed"]:
            print(f"\nQUERY: {r['query']}")
            print(f"  EXPECTED : {r['expected']}")
            print(f"  RETRIEVED: {r['retrieved']}")
            print(f"  MISSED   : {r['missed']}")


if __name__ == "__main__":
    run_evals()
