"""Run minimal OpenAI connectivity and structured-output diagnostics."""

import argparse
import asyncio

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings


class DiagnosticResponse(BaseModel):
    ok: bool


async def diagnose(include_structured: bool) -> None:
    if not settings.openai_api_key:
        raise SystemExit("OPENAI_API_KEY is not loaded.")

    print(f"model={settings.openai_model}")
    print("api_key_loaded=true")

    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
        timeout=settings.openai_timeout_seconds,
        max_retries=0,
    )
    try:
        completion = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_tokens=8,
            temperature=0,
        )
        print(f"plain_completion={completion.choices[0].message.content}")

        if include_structured:
            structured = await client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[{"role": "user", "content": "Return ok=true."}],
                response_format=DiagnosticResponse,
                temperature=0,
            )
            print(f"structured_completion={structured.choices[0].message.parsed}")
    finally:
        await client.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--structured",
        action="store_true",
        help="Also verify a minimal Pydantic structured output.",
    )
    args = parser.parse_args()
    asyncio.run(diagnose(args.structured))


if __name__ == "__main__":
    main()
