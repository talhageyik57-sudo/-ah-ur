"""Ortam değişkenlerinden yapılandırma okuma (harici bağımlılık yok)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

TRUE_VALUES = {"1", "true", "yes", "on", "evet", "acik", "açık"}
FALSE_VALUES = {"0", "false", "no", "off", "hayir", "hayır", "kapali", "kapalı"}


def load_dotenv(path: str | os.PathLike[str] = ".env", override: bool = False) -> dict[str, str]:
    """Basit `.env` okuyucu. Dosya yoksa sessizce boş döner."""
    file = Path(path)
    loaded: dict[str, str] = {}
    if not file.is_file():
        return loaded
    for line in file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        loaded[key] = value
        if override or key not in os.environ:
            os.environ[key] = value
    return loaded


def _as_bool(value: Optional[str], default: bool) -> bool:
    if value is None:
        return default
    text = value.strip().lower()
    if text in TRUE_VALUES:
        return True
    if text in FALSE_VALUES:
        return False
    return default


@dataclass
class Settings:
    """Bot çalışma ayarları."""

    bot_token: Optional[str] = None
    parse_mode: str = "html"
    allowed_chat_ids: frozenset[int] = field(default_factory=frozenset)
    target_chat_id: Optional[str] = None
    finnhub_api_key: Optional[str] = None
    auto_fetch: bool = True
    request_timeout: float = 10.0
    log_level: str = "INFO"

    @classmethod
    def from_env(cls, dotenv_path: str | os.PathLike[str] = ".env") -> "Settings":
        load_dotenv(dotenv_path)
        raw_ids = os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")
        ids = frozenset(
            int(part.strip())
            for part in raw_ids.replace(";", ",").split(",")
            if part.strip().lstrip("-").isdigit()
        )
        return cls(
            bot_token=os.getenv("TELEGRAM_BOT_TOKEN") or None,
            parse_mode=(os.getenv("TELEGRAM_PARSE_MODE") or "html").strip().lower(),
            allowed_chat_ids=ids,
            target_chat_id=(os.getenv("TELEGRAM_TARGET_CHAT_ID") or "").strip() or None,
            finnhub_api_key=os.getenv("FINNHUB_API_KEY") or None,
            auto_fetch=_as_bool(os.getenv("AUTO_FETCH"), True),
            request_timeout=float(os.getenv("REQUEST_TIMEOUT", "10") or 10),
            log_level=(os.getenv("LOG_LEVEL") or "INFO").upper(),
        )

    def is_allowed(self, chat_id: Optional[int]) -> bool:
        """Beyaz liste boşsa herkese açıktır."""
        if not self.allowed_chat_ids:
            return True
        return chat_id is not None and chat_id in self.allowed_chat_ids

    def can_broadcast(self, chat_id: Optional[int]) -> bool:
        """Kanala gönderme yetkisi.

        Beyaz liste boşken kanala gönderime izin verilmez: aksi halde botu
        bulan herkes kanalınıza gönderi attırabilir. Yayın için hedef kanal
        **ve** yetkili kullanıcı listesi birlikte tanımlanmalıdır.
        """
        if not self.target_chat_id or not self.allowed_chat_ids:
            return False
        return chat_id is not None and chat_id in self.allowed_chat_ids

    def broadcast_hint(self) -> str:
        """Yayın kapalıysa nedenini söyleyen mesaj."""
        if not self.target_chat_id:
            return (
                "Hedef kanal tanımlı değil. .env dosyasına "
                "`TELEGRAM_TARGET_CHAT_ID=-100...` satırını ekleyin."
            )
        if not self.allowed_chat_ids:
            return (
                "Güvenlik gereği kanala gönderim için yetkili kullanıcı listesi "
                "zorunludur. .env dosyasına `TELEGRAM_ALLOWED_CHAT_IDS=<sizin id>` "
                "satırını ekleyin."
            )
        return "Bu sohbetin kanala gönderim yetkisi yok."
