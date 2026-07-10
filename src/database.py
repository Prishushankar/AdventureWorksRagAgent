import pyodbc
import pandas as pd

from src.config import config
from src.logger import logger


class DatabaseError(Exception):
    pass


class DatabaseConnection:
    def __init__(self) -> None:
        self._conn: pyodbc.Connection | None = None

    def connect(self) -> pyodbc.Connection:
        if self._conn is None:
            logger.debug("Connecting to database %s on %s", config.db_database, config.db_server)
            self._conn = pyodbc.connect(config.connection_string, autocommit=True)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def execute_query(self, sql: str, params: tuple | None = None) -> pd.DataFrame:
        try:
            conn = self.connect()
            if params:
                df = pd.read_sql(sql, conn, params=params)
            else:
                df = pd.read_sql(sql, conn)
            logger.debug("Query returned %d rows", len(df))
            return df
        except Exception as e:
            raise DatabaseError(str(e)) from e

    def fetch_one(self, sql: str, params: tuple | None = None) -> tuple | None:
        try:
            conn = self.connect()
            cursor = conn.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchone()
        except Exception as e:
            raise DatabaseError(str(e)) from e

    def get_temporal_anchor(self) -> str | None:
        try:
            row = self.fetch_one("""
                SELECT MAX(latest_date) FROM (
                    SELECT MAX(OrderDate) AS latest_date FROM Sales.SalesOrderHeader
                    UNION ALL
                    SELECT MAX(OrderDate) AS latest_date FROM Purchasing.PurchaseOrderHeader
                ) combined
            """)
            if row and row[0]:
                return str(row[0])
            return None
        except DatabaseError as e:
            logger.warning("Temporal anchor lookup failed: %s", e)
            return None

    def get_live_table_columns(self, table_ids: list[str]) -> str:
        tables_to_fetch = [t for t in table_ids if "." in t]
        if not tables_to_fetch:
            return ""

        try:
            pairs = [tuple(t.split(".", 1)) for t in tables_to_fetch]
            placeholders = " OR ".join(["(TABLE_SCHEMA = ? AND TABLE_NAME = ?)"] * len(pairs))
            params: list[str] = []
            for schema, table in pairs:
                params.extend([schema.strip(), table.strip()])

            query = f"""
                SELECT TABLE_SCHEMA, TABLE_NAME, COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE {placeholders}
                ORDER BY TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION
            """
            conn = self.connect()
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            grouped: dict[str, list[str]] = {}
            for schema, table, column in rows:
                grouped.setdefault(f"{schema}.{table}", []).append(column)

            lines = [f"{t}({', '.join(grouped[t])})" for t in tables_to_fetch if t in grouped]
            return "\n".join(lines)
        except Exception as e:
            logger.warning("Live schema lookup failed: %s", e)
            return ""


db = DatabaseConnection()
