import time

import pandas as pd

from src.config import config
from src.intent import clarify_intent
from src.retrieval import retrieve_schema_context
from src.generation import generate_sql
from src.sanitizer import sanitize_sql
from src.executor import execute_sql
from src.logger import logger
from src.explanation import explain_results


def process_user_request(user_query: str, max_retries: int = 4) -> tuple[pd.DataFrame | None, str | None, str | None]:
    start = time.time()

    clarified_query = clarify_intent(user_query)
    logger.info("Query: '%s' | Clarified: '%s'", user_query, clarified_query)

    context = retrieve_schema_context(clarified_query)

    error_msg = ""
    current_sql = ""
    params: tuple | None = None

    for attempt in range(max_retries):
        raw_sql, params = generate_sql(
            clarified_query, context, error_feedback=error_msg, original_query=user_query,
        )

        current_sql = sanitize_sql(raw_sql)

        logger.info("Attempt %d/%d executing SQL:\n%s", attempt + 1, max_retries, current_sql)

        df, db_error = execute_sql(current_sql, params=params)

        if not db_error:
            is_empty_agg = (len(df) == 1 and pd.isna(df.iloc[0, 0])) if len(df) == 1 else False

            if df.empty or is_empty_agg:
                error_msg = (
                    "Query executed but returned 0 rows or a NULL sum. "
                    "WHERE filters were too strict. Use LIKE '%keyword%' instead of '='. "
                    "Broaden date ranges. Rewrite to be more robust."
                )
                logger.warning("Attempt %d: empty result — retrying", attempt + 1)
                continue

            elapsed = time.time() - start
            logger.info("Pipeline succeeded in %.2fs after %d attempt(s)", elapsed, attempt + 1)
            return df, None, current_sql

        logger.warning("Attempt %d failed: %s", attempt + 1, db_error)
        error_msg = f"SQL Server Error: {db_error}. Fix syntax or column names."

    elapsed = time.time() - start
    logger.error("Pipeline failed after %d attempts (%.2fs)", max_retries, elapsed)
    return None, f"Pipeline failed after {max_retries} attempts. Last error: {error_msg}", current_sql
