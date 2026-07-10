import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from src.config import config
from src.pipeline import process_user_request
from src.explanation import explain_results, SUPPORTED_LANGUAGES
from src.logger import logger


def _render_language_picker():
    with st.chat_message("assistant"):
        st.markdown(
            "👋 Before we start — which language would you like me to use for "
            "**describing the results** in? (Your questions can still be in "
            "any language, and the data table itself is unaffected.)"
        )
        cols = st.columns(len(SUPPORTED_LANGUAGES))
        for col, lang in zip(cols, SUPPORTED_LANGUAGES):
            if col.button(lang, key=f"lang_choice_{lang}", use_container_width=True):
                st.session_state.description_language = lang
                st.rerun()


def main() -> None:
    try:
        config.validate()
    except Exception as e:
        st.error(f"Configuration error: {e}")
        st.stop()

    st.set_page_config(page_title="AdventureWorks AI", page_icon="🗄️", layout="wide")
    st.title("🗄️ AdventureWorks Data Assistant")
    st.caption(
        "Ask a business question in any language. I'll write the SQL, fetch the data, and describe it for you."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "description_language" not in st.session_state:
        st.session_state.description_language = None

    if st.session_state.description_language is None:
        _render_language_picker()

    with st.sidebar:
        st.subheader("🌐 Description Language")
        current = st.session_state.description_language or SUPPORTED_LANGUAGES[0]
        chosen = st.radio(
            "Language for result descriptions",
            options=SUPPORTED_LANGUAGES,
            index=SUPPORTED_LANGUAGES.index(current),
            label_visibility="collapsed",
        )
        if chosen != st.session_state.description_language:
            st.session_state.description_language = chosen
            st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("description"):
                st.info(msg["description"])
            if msg.get("sql"):
                st.code(msg["sql"], language="sql")
            if msg.get("df") is not None:
                st.dataframe(msg["df"], use_container_width=True)

    user_query = st.chat_input(
        "E.g., Which bikes are basically dead stock?",
        disabled=st.session_state.description_language is None,
    )

    if user_query:
        st.session_state.messages.append({"role": "user", "content": user_query})
        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing schema and querying database..."):
                df, error, sql = process_user_request(user_query)

            if error:
                st.error(error)
                if sql:
                    st.code(sql, language="sql")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"**Error:** {error}",
                    "sql": sql,
                })
            else:
                response_text = (
                    f"Here is the data you requested. Found **{len(df)}** rows."
                    if df is not None
                    else "Query processed."
                )
                st.markdown(response_text)

                language = st.session_state.description_language or SUPPORTED_LANGUAGES[0]
                with st.spinner(f"Writing description in {language}..."):
                    description = explain_results(user_query, sql, df, language=language)
                st.info(description)

                if sql:
                    st.code(sql, language="sql")
                if df is not None:
                    st.dataframe(df, use_container_width=True)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "description": description,
                    "sql": sql,
                    "df": df,
                })


if __name__ == "__main__":
    main()
