import time
from collections.abc import Callable
from typing import Any

from groq import Groq, RateLimitError

from src.config import config
from src.logger import logger


class LLMError(Exception):
    pass


class LLMClient:
    def __init__(self) -> None:
        self._client: Groq | None = None
        self.total_tokens: int = 0
        self.total_calls: int = 0

    def _lazy_init(self) -> Groq:
        if self._client is None:
            logger.info("Initializing Groq LLM client")
            self._client = Groq(api_key=config.groq_api_key)
        return self._client

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        max_retries: int = 3,
    ) -> str:
        client = self._lazy_init()
        model = model or config.llm_model
        last_error: Exception | None = None

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                self.total_calls += 1
                if response.usage:
                    self.total_tokens += response.usage.total_tokens
                return response.choices[0].message.content.strip()

            except RateLimitError as e:
                wait = min(2 ** attempt * 2, 30)
                logger.warning("Rate limit hit (attempt %d/%d). Retrying in %ds.", attempt + 1, max_retries, wait)
                logger.debug("Rate limit error: %s", e)
                last_error = e
                time.sleep(wait)

            except Exception as e:
                logger.error("LLM call failed (attempt %d/%d): %s: %s", attempt + 1, max_retries, type(e).__name__, e)
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(1)

        raise LLMError(f"LLM call failed after {max_retries} attempts") from last_error

    def generate_with_fallback(
        self,
        messages: list[dict[str, str]],
        fallback: str = "",
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
    ) -> str:
        try:
            return self.generate(messages=messages, model=model, temperature=temperature, max_tokens=max_tokens)
        except LLMError:
            logger.warning("LLM generation failed, using fallback response")
            return fallback


llm_client = LLMClient()
