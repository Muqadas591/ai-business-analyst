"""HTTP adapter for hosted OpenAI-compatible chat-completions APIs."""

from __future__ import annotations

import httpx

from business_analyst.insights.config import InsightSettings


class ProviderError(RuntimeError):
    """Safe application-level provider error."""


class OpenAICompatibleProvider:
    def __init__(self, settings: InsightSettings) -> None:
        settings.validate()
        self._settings = settings

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        url = f"{self._settings.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self._settings.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self._settings.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "max_tokens": self._settings.max_output_tokens,
        }

        try:
            with httpx.Client(
                timeout=self._settings.timeout_seconds,
                follow_redirects=False,
            ) as client:
                response = client.post(
                    url,
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                body = response.json()

            content = body["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ProviderError("The provider returned an empty response.")

            return content

        except ProviderError:
            raise
        except httpx.TimeoutException as exc:
            raise ProviderError("The hosted insight provider timed out.") from exc
        except httpx.HTTPStatusError as exc:
            # Do not include response bodies: they may contain sensitive data.
            raise ProviderError(
                f"The hosted insight provider returned HTTP {exc.response.status_code}."
            ) from exc
        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                "The hosted insight provider returned an invalid response."
            ) from exc
