"""Fiyat yuvarlama, tick adımı ve sayı biçimlendirme yardımcıları.

Small-cap hisselerde seviyelerin "temiz" (psikolojik) rakamlara oturması
önemlidir: 4.5473 gibi bir hedef yerine 4.55, 10.13 yerine 10.10 verilir.
Buradaki fonksiyonlar bu yuvarlamayı fiyat bandına göre yapar.
"""

from __future__ import annotations

import re
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_UP

# (üst sınır, tick adımı) — fiyat bandı büyüdükçe adım da büyür.
TICK_BANDS: tuple[tuple[float, float], ...] = (
    (1.0, 0.01),
    (10.0, 0.05),
    (50.0, 0.10),
    (200.0, 0.25),
)
DEFAULT_TICK = 0.50

_MODES = {"nearest": ROUND_HALF_UP, "up": ROUND_CEILING, "down": ROUND_FLOOR}

_VOLUME_SUFFIXES = {"k": 1e3, "b": 1e9, "m": 1e6, "mn": 1e6, "mln": 1e6, "bn": 1e9}
_NUMBER_RE = re.compile(
    r"^[\$\s%]*([+-]?\d+(?:[.,]\d+)?)\s*(mln|mn|bn|[kmb])?\s*%?$",
    re.IGNORECASE,
)


def tick_size(price: float) -> float:
    """Verilen fiyat için makul en küçük seviye adımı."""
    value = abs(float(price))
    for upper, tick in TICK_BANDS:
        if value < upper:
            return tick
    return DEFAULT_TICK


def round_to(value: float, step: float, mode: str = "nearest") -> float:
    """`value` degerini `step` katlarina yuvarlar (nearest / up / down)."""
    if step <= 0:
        raise ValueError("step pozitif olmalı")
    if mode not in _MODES:
        raise ValueError(f"bilinmeyen yuvarlama modu: {mode}")
    quantum = Decimal(str(float(value))) / Decimal(str(float(step)))
    rounded = quantum.quantize(Decimal(1), rounding=_MODES[mode])
    return float(rounded * Decimal(str(float(step))))


def psych_round(value: float, max_drift: float = 0.015) -> float:
    """Seviyeyi mümkün olan en "temiz" rakama oturtur.

    Kaba adımdan (ör. 0.50) inceye (0.05) doğru denenir; seviyeyi
    `max_drift` oranından fazla kaydıran adım kabul edilmez.
    """
    value = float(value)
    if value <= 0:
        return value
    base = tick_size(value)
    ladder = [base * factor for factor in (10, 5, 2, 1)]

    # Zaten temiz bir adıma oturan seviye kaydırılmaz (4.30 -> 4.30).
    for step in ladder:
        if abs(round_to(value, step, "nearest") - value) < 1e-9:
            return round_to(value, step, "nearest")

    for step in ladder:
        snapped = round_to(value, step, "nearest")
        if snapped > 0 and abs(snapped - value) / value <= max_drift:
            return snapped
    return round_to(value, base, "nearest")


def fmt_price(value: float) -> str:
    """Fiyatı gönderi formatında yazar: 0.4523 / 0.45 / 4.25 / 128.50."""
    v = float(value)
    if v < 1:
        text = f"{v:.4f}".rstrip("0")
        if len(text.partition(".")[2]) < 2:
            return f"{v:.2f}"
        return text
    return f"{v:.2f}"


def fmt_pct(value: float) -> str:
    """Yüzde değişimi `%+32.4` biçiminde yazar."""
    text = f"{float(value):+.2f}".rstrip("0").rstrip(".")
    return f"%{text}"


def fmt_volume(value: float) -> str:
    """Hacmi kısaltır: 1250000 -> 1.25M."""
    v = float(value)
    for suffix, unit in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(v) >= unit:
            return f"{v / unit:.2f}".rstrip("0").rstrip(".") + suffix
    return f"{v:.0f}"


def parse_number(text: str) -> float:
    """"$4,25" / "%32" / "12.5M" gibi girdileri sayıya çevirir."""
    match = _NUMBER_RE.match(str(text).strip())
    if not match:
        raise ValueError(f"sayıya çevrilemedi: {text!r}")
    number = float(match.group(1).replace(",", "."))
    suffix = (match.group(2) or "").lower()
    if suffix:
        number *= _VOLUME_SUFFIXES[suffix]
    return number
