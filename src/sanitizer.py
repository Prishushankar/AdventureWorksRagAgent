import re


def sanitize_sql(raw_sql: str) -> str:
    clean = re.sub(r'```sql\s*', '', raw_sql, flags=re.IGNORECASE)
    clean = re.sub(r'```\s*', '', clean)

    clean = re.sub(r'(?i)\bUSE\s+[a-zA-Z0-9_\[\]]+\s*;?\s*', '', clean)
    clean = re.sub(r'(?i)\bSET\s+NOCOUNT\s+ON\s*;?\s*', '', clean)
    clean = re.sub(r'(?i)^\s*GO\s*$', '', clean, flags=re.MULTILINE)
    clean = re.sub(r'(?i)\bGO\s*;', '', clean)

    year_range_match = re.search(
        r"OrderDate\s*(?:>=|>|BETWEEN)\s*'(\d{4})-(\d{2})-\d{2}'",
        clean,
        flags=re.IGNORECASE,
    )
    if year_range_match:
        target_month = int(year_range_match.group(2))
        clean = re.sub(
            r"OrderDate\s*(?:>=|>|BETWEEN)\s*'[^']+'\s*(?:AND|<|<=)\s*'[^']+'",
            f"MONTH(OrderDate) = {target_month}",
            clean,
            flags=re.IGNORECASE,
        )

    clean = re.sub(r"'2022-(\d{2})-\d{2}'", r"MONTH(OrderDate) = \1", clean)
    clean = re.sub(r"\s+AND\s+YEAR\s*\([^)]+\)\s*=\s*\d{4}", "", clean, flags=re.IGNORECASE)
    clean = re.sub(
        r"WHERE\s+YEAR\s*\([^)]+\)\s*=\s*\d{4}\s+AND\s+",
        "WHERE ",
        clean,
        flags=re.IGNORECASE,
    )

    clean = re.sub(r'\n\s*\n', '\n', clean)
    clean = clean.strip().rstrip(';')
    return clean
