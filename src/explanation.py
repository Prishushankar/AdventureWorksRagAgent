import re

import pandas as pd

from src.config import config
from src.llm_client import llm_client, LLMError
from src.logger import logger


SUPPORTED_LANGUAGES = ["English", "Hindi", "Gujarati", "Marathi"]
DEFAULT_LANGUAGE = "English"

_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_GUJARATI_RE = re.compile(r"[\u0A80-\u0AFF]")

_LANGUAGE_INSTRUCTIONS = {
    "English": "Write the explanation in clear, simple English.",
    "Hindi": (
        "Write the explanation ENTIRELY in the Hindi language, using Devanagari "
        "Unicode script (उदाहरण: यह डेटा दर्शाता है). "
        "Do NOT write Romanized/Latin-letter Hindi (\"Hinglish\") under any circumstances."
    ),
    "Gujarati": (
        "Write the explanation ENTIRELY in the Gujarati language, using Gujarati "
        "Unicode script. Do NOT write Romanized/Latin-letter Gujarati."
    ),
    "Marathi": (
        "Write the explanation ENTIRELY in the Marathi language, using Devanagari "
        "Unicode script. Use Marathi vocabulary (आहे/आहेत), not Hindi (है/हैं)."
    ),
}

_FALLBACK_MESSAGES = {
    "English": {"no_data": "The query ran successfully but returned no matching data.", "summary": "Retrieved {n} row(s) with columns: {cols}."},
    "Hindi": {"no_data": "क्वेरी सफलतापूर्वक चली, लेकिन कोई मिलान डेटा नहीं मिला।", "summary": "{n} पंक्तियाँ मिलीं। कॉलम: {cols}।"},
    "Gujarati": {"no_data": "ક્વેરી સફળતાપૂર્વક ચાલી, પરંતુ કોઈ મેળ ખાતો ડેટા મળ્યો નથી.", "summary": "{n} પંક્તિઓ મળી. કૉલમ: {cols}."},
    "Marathi": {"no_data": "क्वेरी यशस्वीरित्या चालली, पण जुळणारा डेटा आढळला नाही.", "summary": "{n} पंक्ती सापडल्या. स्तंभ: {cols}."},
}


def _normalize_language(language: str) -> str:
    return language if language in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def _fallback_explanation(df: pd.DataFrame | None, language: str = DEFAULT_LANGUAGE) -> str:
    language = _normalize_language(language)
    msgs = _FALLBACK_MESSAGES[language]
    if df is None or df.empty:
        return msgs["no_data"]
    col_list = ", ".join(df.columns.tolist())
    return msgs["summary"].format(n=len(df), cols=col_list)


def _script_is_valid(text: str, language: str) -> bool:
    if language in ("Hindi", "Marathi"):
        return bool(_DEVANAGARI_RE.search(text))
    if language == "Gujarati":
        return bool(_GUJARATI_RE.search(text))
    return True


def explain_results(user_query: str, sql_query: str, df: pd.DataFrame | None, sample_rows: int = 5, language: str = DEFAULT_LANGUAGE) -> str:
    language = _normalize_language(language)

    if df is None or df.empty:
        return _fallback_explanation(df, language)

    sample = df.head(sample_rows).to_dict(orient="records")
    language_instruction = _LANGUAGE_INSTRUCTIONS[language]
    base_prompt = f"""
You are explaining SQL query results to a non-technical business user.

{language_instruction}

User's original question: "{user_query}"

SQL query used:
{sql_query}

Result shape: {len(df)} row(s), columns: {', '.join(df.columns.tolist())}
Sample data (first {min(sample_rows, len(df))} rows): {sample}

In 2-3 short sentences, explain what this data represents. Use specific figures.
Do NOT repeat the SQL. Do NOT use markdown. Do NOT mention you are an AI.
"""
    try:
        explanation = llm_client.generate(
            messages=[{"role": "user", "content": base_prompt}],
            model=config.explanation_model,
            max_tokens=200,
        )

        if not _script_is_valid(explanation, language):
            logger.warning("Explanation failed script check for %s — retrying", language)
            strict_prompt = base_prompt + (
                "\n\nSTRICT: Your previous attempt used the wrong script. "
                "Write ONLY in the requested language/script."
            )
            explanation = llm_client.generate(
                messages=[{"role": "user", "content": strict_prompt}],
                model=config.explanation_model,
                max_tokens=200,
            )

        if not _script_is_valid(explanation, language):
            logger.warning("Explanation still failed script check after retry")
            return _fallback_explanation(df, language)

        return explanation
    except LLMError:
        logger.warning("Explanation generation failed, using fallback")
        return _fallback_explanation(df, language)
