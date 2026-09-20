"""Seviye hesaplama motoru.

Metodoloji (gönderi şablonunun dayandığı kurallar):

* **İlk Direnç**  : gün içi tepe (HOD) veya pre-market tepesi. Yoksa son
  fiyatın %1.5 üzeri varsayılır (fiyat zirveye yakın kabul edilir).
* **İlk Destek**  : gün içi dip (LOD). Gün içi bant çok genişse (>%15) dip
  yerine %38.2 Fibonacci düzeltme pivotu kullanılır — momentum hissesinde
  dip çok uzakta kaldığı için retest bölgesi daha yakındır. Dip yoksa
  günün hareketinin %50 düzeltmesi alınır.
* **Kırılım**     : ilk direncin bir tick + %1 üzeri (ör. 5.00 -> 5.05).
* **TP1**         : direncin %7 üzeri (%5-10 bandı), temiz rakama oturtulur.
* **TP2**         : direncin %20 üzeri (%15-25 bandı).
* **Stop**        : ilk desteğin %2.5 altı (%2-3 bandı).
"""

from __future__ import annotations

from .models import Levels, Quote
from .numbers import fmt_price, psych_round, round_to, tick_size

HIGH_PREMIUM = 0.015          # HOD yoksa direnci fiyatın bu kadar üstüne koy
WIDE_RANGE_RATIO = 0.15       # bu orandan geniş gün içi bant "geniş" sayılır
SHALLOW_RETRACE = 0.382       # geniş bantta destek için Fib düzeltmesi
MID_RETRACE = 0.50            # dip bilinmiyorsa günün hareketinin düzeltmesi
FALLBACK_SUPPORT = 0.94       # hiçbir referans yoksa desteği %6 aşağı koy
BREAKOUT_PREMIUM = 0.01       # kırılım teyidi için direnç üstü pay
TP1_MARGIN = 0.07
TP2_MARGIN = 0.20
STOP_BUFFER = 0.025


def _resistance(quote: Quote, notes: list[str]) -> float:
    """İlk direnç: gün içi / pre-market tepesi, yoksa fiyat üstü tahmin."""
    highs = [h for h in (quote.day_high, quote.premarket_high) if h and h > 0]
    top = max(highs) if highs else None

    if top is not None and top > quote.price:
        label = "gün içi tepe" if top == quote.day_high else "pre-market tepesi"
        notes.append(f"İlk direnç {label} ({fmt_price(top)}) baz alındı.")
        raw = top
    else:
        if top is not None:
            notes.append(
                "Verilen tepe son fiyatın altında kaldığı için (tepe aşılmış) "
                "direnç son fiyatın üzerine taşındı."
            )
        else:
            notes.append(
                "Gün içi tepe verilmediği için direnç son fiyatın "
                f"%{HIGH_PREMIUM * 100:.1f} üzeri kabul edildi."
            )
        raw = quote.price * (1 + HIGH_PREMIUM)

    level = psych_round(raw)
    if level <= quote.price:
        level = round_to(quote.price * (1 + HIGH_PREMIUM), tick_size(quote.price), "up")
    return level


def _support(quote: Quote, resistance: float, notes: list[str]) -> float:
    """İlk destek: gün içi dip, geniş bantta Fib pivotu, yoksa %50 düzeltme."""
    price = quote.price
    tick = tick_size(price)
    low = quote.day_low if quote.day_low and 0 < quote.day_low < price else None

    if low is not None:
        band = resistance - low
        if resistance > 0 and band / resistance > WIDE_RANGE_RATIO:
            raw = resistance - SHALLOW_RETRACE * band
            notes.append(
                f"Gün içi bant geniş (%{band / resistance * 100:.1f}); destek olarak "
                f"dip yerine %38.2 düzeltme pivotu ({fmt_price(raw)}) alındı."
            )
        else:
            raw = low
            notes.append(f"İlk destek gün içi dip ({fmt_price(low)}) baz alındı.")
    else:
        prev_close = quote.implied_prev_close
        if prev_close and 0 < prev_close < price:
            raw = prev_close + MID_RETRACE * (price - prev_close)
            notes.append(
                "Gün içi dip verilmediği için destek, günün hareketinin %50 "
                f"düzeltmesinden ({fmt_price(raw)}) türetildi."
            )
        else:
            raw = price * FALLBACK_SUPPORT
            notes.append(
                "Referans dip/kapanış verisi yok; destek son fiyatın %6 altına kondu."
            )

    level = psych_round(raw)
    if level >= price:
        level = round_to(price * 0.97, tick, "down")
    return max(level, tick)


def compute_levels(quote: Quote) -> Levels:
    """Quote'tan tam seviye setini üretir. Sıralama her zaman tutarlıdır:
    stop < destek < fiyat < direnç < kırılım < TP1 < TP2.
    """
    notes: list[str] = []
    price = quote.price

    resistance = _resistance(quote, notes)
    support = _support(quote, resistance, notes)

    r_tick = tick_size(resistance)
    breakout = round_to(
        resistance + max(r_tick, resistance * BREAKOUT_PREMIUM), r_tick, "up"
    )
    if breakout <= resistance:
        breakout = resistance + r_tick

    tp1 = psych_round(resistance * (1 + TP1_MARGIN))
    if tp1 <= breakout + r_tick:
        tp1 = round_to(breakout + max(2 * r_tick, breakout * 0.03), r_tick, "up")

    tp2 = psych_round(resistance * (1 + TP2_MARGIN))
    if tp2 <= tp1 * 1.03:
        tp2 = round_to(tp1 * 1.08, tick_size(tp1), "up")

    s_tick = tick_size(support)
    stop = round_to(support * (1 - STOP_BUFFER), s_tick, "down")
    if stop >= support:
        stop = support - s_tick
    stop = max(stop, s_tick)

    if quote.day_low and 0 < quote.day_low < support:
        notes.append(
            f"Gün içi dip {fmt_price(quote.day_low)}; stop bu pivotun üzerinde "
            "kalıyorsa sarkmalarda erken stop riski vardır."
        )

    rvol = quote.rvol
    if rvol:
        notes.append(f"RVOL {rvol:.1f}x — kırılım hacim teyidi için referans.")
    if quote.is_squeeze_candidate:
        notes.append("Düşük float + yüksek short oranı: squeeze potansiyeli yüksek.")

    return Levels(
        resistance=resistance,
        support=support,
        breakout_entry=breakout,
        tp1=tp1,
        tp2=tp2,
        stop=stop,
        assumptions=tuple(notes),
    )
