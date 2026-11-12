"""Google Gemini generateContent adapter using the Python standard library."""

import json
import urllib.error
import urllib.parse
import urllib.request

from app.ai.providers.base import ChatProvider, ProviderError


class GeminiProvider(ChatProvider):
    name = "gemini"

    def __init__(self, api_key, model="gemini-2.5-flash", timeout=35):
        self.api_key, self.model, self.timeout = api_key, model, timeout

    def complete(self, messages, *, system_prompt, temperature=0.2):
        if not self.api_key:
            raise ProviderError("Gemini is not configured. Add GEMINI_API_KEY on the server.")
        contents = []
        for message in messages:
            contents.append({"role": "model" if message["role"] == "assistant" else "user",
                             "parts": [{"text": message["content"]}]})
        payload = {"systemInstruction": {"parts": [{"text": system_prompt}]},
                   "contents": contents,
                   "generationConfig": {"temperature": temperature}}
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"{urllib.parse.quote(self.model)}:generateContent")
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json",
                                              "x-goog-api-key": self.api_key}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            parts = data["candidates"][0]["content"]["parts"]
            return "\n".join(part["text"] for part in parts if "text" in part).strip()
        except urllib.error.HTTPError as exc:
            raise ProviderError(f"Gemini request failed (HTTP {exc.code}). Check provider configuration and quota.") from None
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, ValueError):
            raise ProviderError("Gemini could not complete the request. Please try again.") from None
