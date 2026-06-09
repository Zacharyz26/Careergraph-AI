from collections.abc import Awaitable, Callable

from openai import AsyncOpenAI, OpenAIError

from app.core.config import settings

EmbeddingProvider = Callable[[list[str]], Awaitable[list[list[float]]]]


class EmbeddingServiceError(RuntimeError):
    pass


class EmbeddingService:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_embedding_model
        self.provider = provider

    @property
    def is_available(self) -> bool:
        return self.provider is not None or bool(self.api_key)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.provider is not None:
            return await self.provider(texts)
        if not self.api_key:
            raise EmbeddingServiceError("Embedding service is not configured.")

        client = AsyncOpenAI(
            api_key=self.api_key,
            timeout=10,
            max_retries=1,
        )
        try:
            response = await client.embeddings.create(
                model=self.model,
                input=texts,
                encoding_format="float",
            )
        except OpenAIError as exc:
            raise EmbeddingServiceError(
                "Semantic embeddings could not be generated."
            ) from exc
        finally:
            await client.close()

        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]
