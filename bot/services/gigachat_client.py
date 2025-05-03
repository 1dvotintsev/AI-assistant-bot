from __future__ import annotations

"""gigachat_client.py
Асинхронный клиент для REST‑API GigaChat.

Ключевые возможности
--------------------
* автоматическое получение/обновление OAuth‑токена;
* единая `aiohttp.ClientSession` (передаёте свою или
  даёте создать «под капотом»);
* поддержка async‑context‑manager (`async with GigaChatClient() as gc:`);
* параметры client_id/client_secret могут браться
  из аргументов, из `config.py` *или* из переменных
  окружения – что найдётся первым.
"""

import base64
import os
import time
import uuid
from typing import Any, Dict, List, Optional
from aiohttp import TCPConnector
import aiohttp

__all__ = ["GigaChatClient", "GIGACHAT_OAUTH_URL", "GIGACHAT_CHAT_URL"]

# --- Константы API -----------------------------------------------------------
GIGACHAT_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

# --- Пытаемся подтянуть секреты из config.py --------------------------------
try:
    from config import (  # type: ignore
        GIGACHAT_CLIENT_ID as _CFG_ID,
        GIGACHAT_CLIENT_SECRET as _CFG_SECRET,
    )
except ModuleNotFoundError:
    _CFG_ID = None
    _CFG_SECRET = None

# --- Класс клиента -----------------------------------------------------------
class GigaChatClient:
    """Лёгкий асинхронный враппер над GigaChat.

    Пример использования::

        from gigachat_client import GigaChatClient

        async with GigaChatClient() as gc:
            answer = await gc.chat([
                {"role": "user", "content": "Привет, кто ты?"}
            ])
            print(answer)
    """

    def __init__(
        self,
        *,
        client_id: str | None = None,
        client_secret: str | None = None,
        scope: str = "GIGACHAT_API_PERS",
        session: aiohttp.ClientSession | None = None,
        timeout: int = 30,
    ) -> None:
        # ── где взять id/secret ──────────────────────────────────────────
        self._client_id = client_id or _CFG_ID or os.getenv("GIGACHAT_CLIENT_ID")
        self._client_secret = (
            client_secret or _CFG_SECRET or os.getenv("GIGACHAT_CLIENT_SECRET")
        )
        if not (self._client_id and self._client_secret):
            raise RuntimeError(
                "GigaChat credentials are not set. "
                "Provide client_id/client_secret or define them in config.py / env."
            )

        # ── базовый токен для OAuth (ОДНО кодирование) ───────────────────
        # ── где взять id/secret ──────────────────────────────────────────
        self._client_id = client_id or _CFG_ID or os.getenv("GIGACHAT_CLIENT_ID")
        self._client_secret = (
            client_secret or _CFG_SECRET or os.getenv("GIGACHAT_CLIENT_SECRET")
        )
        if not (self._client_id and self._client_secret):
            raise RuntimeError("GigaChat credentials not set.")

        # --- ситуация, когда secret = BASE64(client_id:real_secret) -----
        try:
            decoded = base64.b64decode(self._client_secret, validate=True).decode()
            if ":" in decoded:                          # да, это пара «id:secret»
                cid_decoded, real_secret = decoded.split(":", 1)
                # если id в коде = id из расшифровки – берём настоящий secret
                if cid_decoded == self._client_id:
                    self._client_secret = real_secret
        except Exception:
            # secret был не base64 – игнорируем, всё нормально
            pass

        # ── финальный Basic-ключ (одно кодирование!) ────────────────────
        self._basic_auth = base64.b64encode(
            f"{self._client_id}:{self._client_secret}".encode()
        ).decode()

        self._scope = scope
        self._token: Optional[str] = None
        self._expires_at_ms: int = 0

        self._external_session = session is not None
        self._session = session or aiohttp.ClientSession(
            connector=TCPConnector(ssl=False),              # ← временно без проверки SSL
            timeout=aiohttp.ClientTimeout(total=timeout),
        )


    # ──────────────────────────────────────────────────────────────────────────
    # public API
    # ──────────────────────────────────────────────────────────────────────────
    async def chat(
        self,
        messages: List[Dict[str, Any]],
        *,
        model: str = "GigaChat",
        **params: Any,
    ) -> str:
        """Отправить сообщения в /chat/completions и вернуть ответ модели."""
        await self._ensure_token()
        payload = {"model": model, "messages": messages, **params}

        async with self._session.post(
            GIGACHAT_CHAT_URL,
            json=payload,
            headers={"Authorization": f"Bearer {self._token}"},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            return data["choices"][0]["message"]["content"]

    async def close(self) -> None:  # noqa: D401: imperative mood here is OK
        """Закрыть `aiohttp`‑сессию (если создали внутри)."""
        if not self._external_session:
            await self._session.close()

    # ────────────────────────── context manager ──────────────────────────────
    async def __aenter__(self) -> "GigaChatClient":
        return self

    async def __aexit__(self, *_exc) -> None:  # noqa: D401
        await self.close()

    # ──────────────────────────── internals ──────────────────────────────────
    async def _ensure_token(self) -> None:
        """Берёт новый OAuth‑токен, если текущий протухает < 15 c."""
        if self._token and time.time() * 1000 < self._expires_at_ms - 15_000:
            return

        rq_uid = str(uuid.uuid4())
        async with self._session.post(
            GIGACHAT_OAUTH_URL,
            data={"scope": self._scope},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": rq_uid,
                "Authorization": f"Basic {self._basic_auth}",
            },
        ) as resp:
            resp.raise_for_status()
            token_data = await resp.json()
            self._token = token_data["access_token"]
            self._expires_at_ms = int(token_data["expires_at"])
