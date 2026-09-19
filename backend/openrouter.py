"""OpenRouter API client for making LLM requests."""

import httpx
from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL


import asyncio
import random

async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    max_retries: int = 4,
    max_tokens: int = 4096
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API with automatic retry on rate limits.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds
        max_retries: Number of retries for 429 rate limit or network errors
        max_tokens: Maximum tokens in response completion

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "LLM Council",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }

    backoff_delays = [2.0, 4.0, 7.0, 11.0, 15.0]

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload
                )

                if response.status_code == 429 and attempt < max_retries:
                    base_delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                    wait_time = base_delay + random.uniform(0.5, 2.0)
                    print(f"Rate limited (429) for {model}. Backing off for {wait_time:.1f}s (attempt {attempt+1}/{max_retries})...")
                    await asyncio.sleep(wait_time)
                    continue

                response.raise_for_status()

                data = response.json()
                message = data['choices'][0]['message']

                raw_content = message.get('content')
                if raw_content is None:
                    raw_content = ''

                return {
                    'content': raw_content,
                    'reasoning_details': message.get('reasoning_details')
                }

        except Exception as e:
            if attempt < max_retries and ("429" in str(e) or "522" in str(e) or "503" in str(e)):
                base_delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                wait_time = base_delay + random.uniform(0.5, 2.0)
                print(f"Retrying {model} after status error ({e}): {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
                continue
            print(f"Error querying model {model} (attempt {attempt+1}): {e}")
            if attempt == max_retries:
                return None

    return None


async def query_model_stream(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0,
    max_retries: int = 3,
    max_tokens: int = 4096
):
    """
    Query a single model via OpenRouter API with SSE streaming.
    Yields token strings as they arrive in real-time.

    Args:
        model: OpenRouter model identifier
        messages: List of message dicts
        timeout: Request timeout
        max_retries: Number of retries on 429 errors
        max_tokens: Maximum tokens in response completion

    Yields:
        str: Content tokens/deltas as they arrive
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "LLM Council",
    }

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
    }

    backoff_delays = [2.0, 4.0, 7.0, 11.0]

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    OPENROUTER_API_URL,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status_code == 429 and attempt < max_retries:
                        base_delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                        wait_time = base_delay + random.uniform(0.5, 2.0)
                        print(f"Rate limited (429) for stream {model}. Retrying in {wait_time:.1f}s...")
                        await asyncio.sleep(wait_time)
                        continue

                    response.raise_for_status()

                    import json
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue

                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

                    return

        except Exception as e:
            if attempt < max_retries and ("429" in str(e) or "522" in str(e) or "503" in str(e)):
                base_delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                wait_time = base_delay + random.uniform(0.5, 2.0)
                await asyncio.sleep(wait_time)
                continue

            print(f"Error streaming from {model} (attempt {attempt+1}): {e}")
            if attempt == max_retries:
                # Fallback to non-streaming query
                try:
                    res = await query_model(model, messages, timeout=timeout, max_tokens=max_tokens)
                    if res and res.get('content'):
                        yield res['content']
                except Exception as fb_err:
                    print(f"Fallback non-streaming query failed for {model}: {fb_err}")
                return


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]],
    stagger_seconds: float = 0.4,
    max_tokens: int = 4096
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel with staggered dispatch to avoid burst rate limits.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model
        stagger_seconds: Small delay between launching concurrent tasks to avoid 429 burst
        max_tokens: Maximum tokens per model response

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    async def _staggered_query(model: str, delay: float):
        if delay > 0:
            await asyncio.sleep(delay)
        return await query_model(model, messages, max_tokens=max_tokens)

    tasks = [_staggered_query(model, i * stagger_seconds) for i, model in enumerate(models)]
    responses = await asyncio.gather(*tasks)

    return {model: response for model, response in zip(models, responses)}

