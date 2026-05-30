import asyncio
import logging
from datetime import datetime
from typing import AsyncIterator, Optional

from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        max_tokens: int = 2000,
        temperature: float = 0.3,
        max_concurrent: int = 3,
    ):
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._last_call_time = 0.0
        self._min_interval = 2.0  # seconds between calls

    async def chat(self, messages: list[dict], **kwargs) -> Optional[str]:
        async with self._semaphore:
            elapsed = datetime.utcnow().timestamp() - self._last_call_time
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)

            try:
                response = await self.client.chat.completions.create(
                    model=kwargs.get("model", self.model),
                    messages=messages,
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", self.temperature),
                )
                self._last_call_time = datetime.utcnow().timestamp()
                return response.choices[0].message.content
            except Exception as e:
                logger.error(f"DeepSeek API error: {e}")
                return None

    async def chat_stream(self, messages: list[dict], **kwargs) -> AsyncIterator[str]:
        async with self._semaphore:
            elapsed = datetime.utcnow().timestamp() - self._last_call_time
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            try:
                stream = await self.client.chat.completions.create(
                    model=kwargs.get("model", self.model),
                    messages=messages,
                    max_tokens=kwargs.get("max_tokens", self.max_tokens),
                    temperature=kwargs.get("temperature", self.temperature),
                    stream=True,
                )
                async for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                self._last_call_time = datetime.utcnow().timestamp()
            except Exception as e:
                logger.error(f"DeepSeek stream error: {e}")
                yield ""

    async def analyze_json(self, messages: list[dict], **kwargs) -> Optional[str]:
        messages_with_format = messages.copy()
        messages_with_format.append({
            "role": "system",
            "content": "Respond with valid JSON only. No markdown, no backticks.",
        })
        return await self.chat(messages_with_format, **kwargs)
