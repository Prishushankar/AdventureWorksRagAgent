from src.llm_client import llm_client
from src.logger import logger


def clarify_intent(user_query: str) -> str:
    prompt = f"""You are an AI assistant helping a user query a SQL Server database.
The user may ask in Hinglish (Hindi + English mix) or English.
Translate the question into a clear, concise English data intent query.
If already in English, return it as-is.

--- CRITICAL TRANSLATION RULES ---
1. Remove conversational filler words (e.g., 'aise', 'aasie', 'kon se', 'wale', 'wala', 'bhaiya').
2. DOMAIN TERMINOLOGY STANDARDIZATION:
   - "dead stock" MUST produce: "What is the dead stock for..."
   - "late" -> "late shipment" or "late delivery"
   - "kitne" / "how many" -> "Count the number of..." or "What is the total sum of..."

Return ONLY the clarified English question, nothing else. No markdown.

User Query: '{user_query}'"""
    try:
        result = llm_client.generate(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
        )
        logger.debug("Intent clarified: '%s' -> '%s'", user_query, result)
        return result
    except Exception:
        logger.warning("Intent clarification failed, using original query")
        return user_query
