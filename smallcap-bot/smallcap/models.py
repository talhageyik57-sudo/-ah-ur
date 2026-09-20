"""Girdi (Quote) ve hesaplanmış seviye (Levels) veri yapıları."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional

from .numbers import fmt_volume


@dataclass(frozen=True)
class Quote:
    """Bir hissenin analiz için gereken ham verisi.

    Zorunlu alanlar `ticker` ve `price`. Diğer alanlar verildikçe seviyeler
    tahminle değil gerçek veriyle hesaplanır.
    """

    ticker: str
    price: float
    change_pct: Optional[float] = None
    catalyst: Optional[str] = None
    day_high: Optional[float] = None
    day_low: Optional[float] = None
    premarket_high: Optional[float] = None
    prev_close: Optional[float] = None
    volume: Optional[float] = None
    avg_volume: Optional[float] = None
    float_shares: Optional[float] = None
    short_float: Optional[float] = None
    source: str = "manuel"

    def __post_init__(self) -> None:
        ticker = str(self.ticker or "").strip().lstrip("$").upper()
        if not ticker or not ticker.replace(".", "").replace("-", "").isalnum():
            raise ValueError(f"geçersiz hisse kodu: {self.ticker!r}")
        object.__setattr__(self, "ticker", ticker)

        try:
            price = float(self.price)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"geçersiz fiyat: {self.price!r}") from exc
        if price <= 0:
            raise ValueError("fiyat pozitif olmalı")
        object.__setattr__(self, "price", price)

        for field in (
            "change_pct",
            "day_high",
            "day_low",
            "premarket_high",
            "prev_close",
            "volume",
            "avg_volume",
            "float_shares",
            "short_float",
        ):
            value = getattr(self, field)
            if value is None:
                continue
            object.__setattr__(self, field, float(value))

        catalyst = (self.catalyst or "").strip()
        object.__setattr__(self, "catalyst", catalyst or None)

    @property
    def rvol(self) -> Optional[float]:
        """Göreceli hacim (RVOL) — hacim / ortalama hacim."""
        if self.volume and self.avg_volume and self.avg_volume > 0:
            return self.volume / self.avg_volume
        return None

    @property
    def is_squeeze_candidate(self) -> bool:
        """Düşük float + yüksek short oranı = squeeze adayı."""
        low_float = self.float_shares is not None and self.float_shares <= 20_000_000
        high_short = self.short_float is not None and self.short_float >= 15.0
        return low_float and high_short

    @property
    def implied_prev_close(self) -> Optional[float]:
        """Önceki kapanış verilmediyse yüzde değişimden türetir."""
        if self.prev_close and self.prev_close > 0:
            return self.prev_close
        if self.change_pct is not None and self.change_pct > -100:
            return self.price / (1 + self.change_pct / 100.0)
        return None

    def merge(self, other: "Quote") -> "Quote":
        """Eksik alanları `other` ile tamamlar; mevcut alanlara dokunmaz."""
        updates = {}
        for field in (
            "change_pct",
            "catalyst",
            "day_high",
            "day_low",
            "premarket_high",
            "prev_close",
            "volume",
            "avg_volume",
            "float_shares",
            "short_float",
        ):
            if getattr(self, field) is None and getattr(other, field) is not None:
                updates[field] = getattr(other, field)
        return replace(self, **updates) if updates else self

    def summary(self) -> str:
        """Tek satırlık teknik özet — /detay çıktısında kullanılır."""
        parts = [f"{self.ticker} @ {self.price}"]
        if self.change_pct is not None:
            parts.append(f"değişim {self.change_pct:+.2f}%")
        if self.day_high:
            parts.append(f"HOD {self.day_high}")
        if self.day_low:
            parts.append(f"LOD {self.day_low}")
        if self.premarket_high:
            parts.append(f"PM {self.premarket_high}")
        if self.volume:
            parts.append(f"hacim {fmt_volume(self.volume)}")
        if self.rvol:
            parts.append(f"RVOL {self.rvol:.1f}x")
        if self.float_shares:
            parts.append(f"float {fmt_volume(self.float_shares)}")
        if self.short_float is not None:
            parts.append(f"short {self.short_float:.1f}%")
        parts.append(f"kaynak: {self.source}")
        return " | ".join(parts)


@dataclass(frozen=True)
class Levels:
    """Hesaplanmış teknik seviyeler ve hesap gerekçeleri."""

    resistance: float
    support: float
    breakout_entry: float
    tp1: float
    tp2: float
    stop: float
    assumptions: tuple[str, ...] = ()

    @property
    def risk(self) -> float:
        """Giriş ile stop arası mesafe (birim risk)."""
        return self.breakout_entry - self.stop

    @property
    def reward_tp1(self) -> float:
        return self.tp1 - self.breakout_entry

    @property
    def reward_tp2(self) -> float:
        return self.tp2 - self.breakout_entry

    @property
    def rr_tp1(self) -> Optional[float]:
        return self.reward_tp1 / self.risk if self.risk > 0 else None

    @property
    def rr_tp2(self) -> Optional[float]:
        return self.reward_tp2 / self.risk if self.risk > 0 else None
