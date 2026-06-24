from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypeVar

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

from app.core.config import settings

SchemaT = TypeVar("SchemaT", bound=BaseModel)
logger = logging.getLogger(__name__)


class LLMServiceError(RuntimeError):
    """Base error for structured LLM generation failures."""


class MissingAPIKeyError(LLMServiceError):
    pass


class LLMResponseError(LLMServiceError):
    pass


MockResponseFactory = Callable[[type[SchemaT]], SchemaT]


class LLMService:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
        mock_response_factory: MockResponseFactory | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_model
        self.base_url = (
            base_url if base_url is not None else settings.openai_base_url
        )
        self.timeout_seconds = (
            timeout_seconds
            if timeout_seconds is not None
            else settings.openai_timeout_seconds
        )
        self.max_retries = (
            max_retries
            if max_retries is not None
            else settings.openai_max_retries
        )
        self.mock_response_factory = mock_response_factory

    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[SchemaT],
    ) -> SchemaT:
        if self.mock_response_factory is not None:
            return self.mock_response_factory(response_model)

        if not self.api_key:
            raise MissingAPIKeyError(
                "OPENAI_API_KEY is not configured. Add it to backend/.env "
                "before calling an LLM parsing endpoint."
            )

        client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout_seconds,
            max_retries=self.max_retries,
        )
        try:
            request_options = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": response_model,
            }
            try:
                completion = await client.beta.chat.completions.parse(
                    **request_options,
                    temperature=0,
                )
            except BadRequestError as exc:
                if not self._is_unsupported_temperature_error(exc):
                    raise
                logger.info(
                    "Retrying structured generation without temperature: model=%s request_id=%s",
                    self.model,
                    getattr(exc, "request_id", None),
                )
                completion = await client.beta.chat.completions.parse(
                    **request_options,
                )
        except OpenAIError as exc:
            self._log_provider_error(exc)
            raise LLMServiceError(self._public_provider_error(exc)) from exc
        except ValidationError as exc:
            logger.exception(
                "OpenAI structured response failed Pydantic validation: "
                "model=%s schema=%s error=%s",
                self.model,
                response_model.__name__,
                self._sanitize(str(exc)),
            )
            raise LLMResponseError(
                "The OpenAI response did not match the requested schema "
                f"({type(exc).__name__})."
            ) from exc
        finally:
            await client.close()

        if not completion.choices:
            raise LLMResponseError("The LLM returned no structured output.")
        message = completion.choices[0].message
        if message.refusal:
            raise LLMResponseError(f"The LLM refused the request: {message.refusal}")
        if message.parsed is None:
            raise LLMResponseError(
                "The LLM returned no schema-valid structured output."
            )
        return message.parsed

    def _log_provider_error(self, exc: OpenAIError) -> None:
        logger.exception(
            "OpenAI structured generation failed: type=%s model=%s status=%s "
            "code=%s request_id=%s error=%s",
            type(exc).__name__,
            self.model,
            getattr(exc, "status_code", None),
            getattr(exc, "code", None),
            getattr(exc, "request_id", None),
            self._sanitize(str(exc)),
        )

    def _public_provider_error(self, exc: OpenAIError) -> str:
        if isinstance(exc, APITimeoutError):
            return "The analysis is taking longer than expected. Please try again."
        if isinstance(exc, AuthenticationError):
            return "The AI analysis service is temporarily unavailable."
        if isinstance(exc, RateLimitError):
            return "The AI analysis service is busy. Please try again later."
        if isinstance(exc, (PermissionDeniedError, NotFoundError)):
            return "The AI analysis service is temporarily unavailable."
        if isinstance(exc, BadRequestError):
            return "The analysis could not be completed. Please try again."
        if isinstance(exc, APIConnectionError):
            return "The AI analysis service could not be reached. Please try again."
        if isinstance(exc, APIStatusError):
            return "The AI analysis service is temporarily unavailable."
        return "The analysis could not be completed. Please try again."

    def _sanitize(self, message: str) -> str:
        if self.api_key:
            return message.replace(self.api_key, "[REDACTED]")
        return message

    def _is_unsupported_temperature_error(self, exc: BadRequestError) -> bool:
        message = str(exc).casefold()
        return "temperature" in message and "unsupported" in message
