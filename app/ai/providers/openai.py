"""OpenAI Chat Completions adapter using the Python standard library."""

import json
import urllib.error
import urllib.request

from app.ai.providers.base import ChatProvider, ProviderError


class OpenAIProvider(ChatProvider):
    name = "openai"

    def __init__(self, api_key, model="gpt-4.1-mini", timeout=35):
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def complete(self, messages, *, system_prompt, temperature=0.2):
        if not self.api_key:
            raise ProviderError("OpenAI is not configured. Add OPENAI_API_KEY on the server.")
        payload = {"model": self.model, "temperature": temperature,
                   "messages": [{"role": "system", "content": system_prompt}, *messages]}
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as exc:
            raise ProviderError(f"OpenAI request failed (HTTP {exc.code}). Check provider configuration and quota.") from None
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError):
            raise ProviderError("OpenAI could not complete the request. Please try again.") from None
