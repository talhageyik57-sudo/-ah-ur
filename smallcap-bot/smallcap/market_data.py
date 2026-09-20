"""İsteğe bağlı canlı fiyat verisi.

Sağlayıcı sırası: Finnhub (API anahtarı varsa, yalnızca stdlib ile) ->
yfinance (kuruluysa). Hiçbiri kullanılamazsa `None` döner ve bot manuel
girdiyle çalışmaya devam eder.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from .models import Quote

logger = logging.getLogger(__name__)

FINNHUB_URL = "https://finnhub.io/api/v1/quote"


def fetch_quote(
    ticker: str,
    finnhub_api_key: Optional[str] = None,
    timeout: float = 10.0,
) -> Optional[Quote]:
    """Hisse için canlı veri getirir; başarısız olursa `None`."""
    ticker = ticker.strip().lstrip("$").upper()
    for provider in (_from_finnhub, _from_yfinance):
        try:
            quote = provider(ticker, finnhub_api_key, timeout)
        except Exception as exc:  # sağlayıcı hatası botu düşürmemeli
            logger.warning("%s canlı veri alınamadı (%s): %s", ticker, provider.__name__, exc)
            continue
        if quote is not None:
            return quote
    return None


def _from_finnhub(ticker: str, api_key: Optional[str], timeout: float) -> Optional[Quote]:
    if not api_key:
        return None
    query = urllib.parse.urlencode({"symbol": ticker, "token": api_key})
    request = urllib.request.Request(
        f"{FINNHUB_URL}?{query}",
        headers={"User-Agent": "smallcap-breakout-bot/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))

    price = payload.get("c")
    if not price:
        return None
    return Quote(
        ticker=ticker,
        price=price,
        change_pct=payload.get("dp"),
        day_high=payload.get("h") or None,
        day_low=payload.get("l") or None,
        prev_close=payload.get("pc") or None,
        source="finnhub",
    )


def _from_yfinance(ticker: str, api_key: Optional[str], timeout: float) -> Optional[Quote]:
    try:
        import yfinance  # type: ignore
    except ImportError:
        return None

    handle = yfinance.Ticker(ticker)
    fast = getattr(handle, "fast_info", None) or {}

    def _get(*names):
        for name in names:
            value = None
            try:
                value = fast[name]  # type: ignore[index]
            except Exception:
                value = getattr(fast, name, None)
            if value:
                return float(value)
        return None

    price = _get("last_price", "lastPrice")
    if not price:
        return None
    prev_close = _get("previous_close", "previousClose")
    change_pct = ((price / prev_close) - 1) * 100 if prev_close else None

    float_shares = short_float = avg_volume = None
    try:
        info = handle.get_info()
        float_shares = info.get("floatShares")
        short_percent = info.get("shortPercentOfFloat")
        short_float = short_percent * 100 if short_percent else None
        avg_volume = info.get("averageVolume")
    except Exception as exc:  # info uç noktası sık sık boş döner
        logger.debug("%s yfinance info alınamadı: %s", ticker, exc)

    return Quote(
        ticker=ticker,
        price=price,
        change_pct=change_pct,
        day_high=_get("day_high", "dayHigh"),
        day_low=_get("day_low", "dayLow"),
        prev_close=prev_close,
        volume=_get("last_volume", "lastVolume"),
        avg_volume=avg_volume,
        float_shares=float_shares,
        short_float=short_float,
        source="yfinance",
    )
