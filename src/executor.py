import pandas as pd

from src.database import db, DatabaseError
from src.logger import logger


FORBIDDEN_KEYWORDS = {"DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE", "ALTER", "CREATE", "EXEC", "EXECUTE"}


class ExecutionError(Exception):
    pass


def execute_sql(sql_query: str, params: tuple | None = None) -> tuple[pd.DataFrame | None, str | None]:
    tokens = sql_query.upper().split()
    if any(word in FORBIDDEN_KEYWORDS for word in tokens):
        logger.warning("Security block: forbidden keyword in query")
        return None, "Security block - Data modification is not allowed."

    try:
        df = db.execute_query(sql_query, params=params)
        return df, None
    except DatabaseError as e:
        return None, str(e)
