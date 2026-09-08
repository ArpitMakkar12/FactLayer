from __future__ import annotations

import json
import time
from typing import Any

import httpx

from app.settings import settings


def complete_json(prompt: str, model: str | None = None) -> dict[str, Any] | None:
    if not settings.llm_api_key:
        return None
    url = settings.llm_base_url.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "model": model or settings.llm_model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
    }
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with httpx.Client(timeout=90.0) as client:
                r = client.post(url, headers=headers, json=body)
                if r.status_code == 429:
                    time.sleep(2**attempt)
                    continue
                r.raise_for_status()
                content = r.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except Exception as exc:
            last_err = exc
            time.sleep(2**attempt)
    _ = last_err
    return None
