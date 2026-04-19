from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from common import DEFAULT_KG2API_TIMEOUT, get_env_value, load_env_values, normalize_whitespace


class KG2ApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


@dataclass(frozen=True)
class KG2ApiSettings:
    base_url: str
    api_key: str
    timeout: float = DEFAULT_KG2API_TIMEOUT


def load_kg2api_settings(env_path: Path, params: dict[str, Any] | None = None) -> KG2ApiSettings:
    overrides = params or {}
    env_values = load_env_values(env_path)
    base_url = normalize_whitespace(
        overrides.get("kg2api_base_url")
        or get_env_value(env_values, "KG2API_BASE_URL")
    )
    api_key = normalize_whitespace(
        overrides.get("kg2api_api_key")
        or get_env_value(env_values, "KG2API_API_KEY")
    )
    timeout_text = normalize_whitespace(
        overrides.get("kg2api_timeout")
        or get_env_value(env_values, "KG2API_TIMEOUT")
    )
    timeout = float(timeout_text) if timeout_text else float(DEFAULT_KG2API_TIMEOUT)

    if not base_url:
        raise ValueError(f"Missing KG2API_BASE_URL in {env_path}")
    if not api_key:
        raise ValueError(f"Missing KG2API_API_KEY in {env_path}")
    return KG2ApiSettings(base_url=base_url.rstrip("/"), api_key=api_key, timeout=timeout)


class KG2ApiClient:
    def __init__(self, settings: KG2ApiSettings) -> None:
        import httpx

        self.settings = settings
        self._httpx = httpx
        self._client = httpx.Client(
            base_url=settings.base_url,
            timeout=settings.timeout,
            headers={
                "Content-Type": "application/json",
                "X-API-Key": settings.api_key,
            },
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "KG2ApiClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._client.post(path, json=payload)
        except self._httpx.TimeoutException as exc:
            raise KG2ApiError(f"KG2API request timed out for {path}") from exc
        except self._httpx.HTTPError as exc:
            raise KG2ApiError(f"KG2API request failed for {path}: {exc}") from exc

        raw_body = response.text
        try:
            body = response.json()
        except ValueError:
            body = None

        if response.status_code >= 400:
            detail = None
            if isinstance(body, dict):
                detail = body.get("detail") or body.get("error") or body.get("message")
            message = normalize_whitespace(detail) or raw_body or f"HTTP {response.status_code}"
            raise KG2ApiError(
                f"KG2API {path} returned {response.status_code}: {message}",
                status_code=response.status_code,
                payload=body,
            )

        if not isinstance(body, dict):
            raise KG2ApiError(f"KG2API {path} returned a non-object response", payload=body)
        return body

    def search(self, *, idea_text: str | None = None, pdf_path: str | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if normalize_whitespace(idea_text):
            payload["idea_text"] = idea_text
        if normalize_whitespace(pdf_path):
            payload["pdf_path"] = pdf_path
        if options:
            payload["options"] = options
        return self._request("/v1/search", payload)

    def authors_related(self, *, idea_text: str | None = None, pdf_path: str | None = None, options: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if normalize_whitespace(idea_text):
            payload["idea_text"] = idea_text
        if normalize_whitespace(pdf_path):
            payload["pdf_path"] = pdf_path
        if options:
            payload["options"] = options
        return self._request("/v1/authors/related", payload)

    def authors_support_papers(self, *, query_text: str, authors: list[dict[str, Any]], options: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "query_text": query_text,
            "authors": authors,
        }
        if options:
            payload["options"] = options
        return self._request("/v1/authors/support-papers", payload)

    def authors_papers(self, *, identifier: str, search_by: str, options: dict[str, Any] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "identifier": identifier,
            "search_by": search_by,
        }
        if options:
            payload["options"] = options
        return self._request("/v1/authors/papers", payload)
