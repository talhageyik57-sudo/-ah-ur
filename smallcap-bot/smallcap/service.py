"""Girdi metninden hazır Telegram gönderisine kadar olan akış.

Hem Telegram bot katmanı hem de CLI bu modülü kullanır.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Optional

from .config import Settings
from .levels import compute_levels
from .market_data import fetch_quote
from .models import Quote
from .parser import USAGE, ParseError, parse_fields
from .template import render_details, render_post

logger = logging.getLogger(__name__)


def build_quote(text: str, settings: Optional[Settings] = None) -> Quote:
    """Metni çözümler, gerekirse canlı veriyle tamamlar.

    Kullanıcının verdiği değerler her zaman canlı veriyi ezer — elle
    girilen pre-market tepesi API'nin bilmediği bir seviyedir.
    """
    settings = settings or Settings()
    parsed = parse_fields(text)

    live: Optional[Quote] = None
    if settings.auto_fetch:
        live = fetch_quote(
            parsed.ticker,
            finnhub_api_key=settings.finnhub_api_key,
            timeout=settings.request_timeout,
        )

    if parsed.has_price:
        quote = parsed.to_quote()
        if live is None:
            return quote
        merged = quote.merge(live)
        if merged is not quote:
            merged = replace(merged, source=f"manuel + {live.source}")
        return merged

    if live is None:
        raise ParseError(
            f"${parsed.ticker} için fiyat verilmedi ve canlı veri sağlayıcısı "
            f"kullanılamıyor.\n\n{USAGE}"
        )

    overrides = {key: value for key, value in parsed.fields.items() if value is not None}
    return replace(live, **overrides) if overrides else live


def analyze(text: str, settings: Optional[Settings] = None, parse_mode: Optional[str] = None) -> str:
    """Telegram'a atılmaya hazır gönderi metnini döndürür."""
    settings = settings or Settings()
    quote = build_quote(text, settings)
    levels = compute_levels(quote)
    return render_post(quote, levels, parse_mode or settings.parse_mode)


def analyze_details(
    text: str, settings: Optional[Settings] = None, parse_mode: Optional[str] = None
) -> str:
    """Seviyelerin nasıl hesaplandığını gösteren kontrol çıktısı."""
    settings = settings or Settings()
    quote = build_quote(text, settings)
    levels = compute_levels(quote)
    return render_details(quote, levels, parse_mode or settings.parse_mode)
