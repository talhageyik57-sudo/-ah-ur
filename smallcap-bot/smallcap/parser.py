"""Serbest metin girdisini yapılandırılmış veriye çevirir.

Desteklenen girdi biçimleri::

    RKLB 4.25 %32 FDA onayı sonrası hacim patlaması
    $ABCD 0.4523 +118% hod=0.52 lod=0.31 vol=48M avgvol=1.2M
    SOUN 12.40 -3.2 float=18M short=22% haber=Nvidia ortaklığı

Kural: ilk kelime hisse kodu, ardından gelen sayı son fiyat, `%` veya
işaret taşıyan sayı yüzde değişim, kalan metin katalizör. `anahtar=değer`
çiftleri metnin herhangi bir yerinde bulunabilir.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from .models import Quote
from .numbers import parse_number

USAGE = (
    "Kullanım: <HİSSE> <FİYAT> <%DEĞİŞİM> <haber metni>\n"
    "Örnek: RKLB 4.25 %32 FDA onayı sonrası hacim patlaması\n"
    "Ek alanlar: hod= lod= pm= pc= vol= avgvol= float= short= haber="
)

# alan adı -> kabul edilen anahtarlar
ALIASES: dict[str, tuple[str, ...]] = {
    "price": ("fiyat", "price", "son", "sonfiyat", "last", "p"),
    "change_pct": ("degisim", "değişim", "change", "chg", "yuzde", "yüzde", "pct", "oran"),
    "day_high": ("hod", "high", "yuksek", "yüksek", "tepe", "zirve", "gunyuksek"),
    "day_low": ("lod", "low", "dusuk", "düşük", "dip", "taban", "gundip"),
    "premarket_high": ("pm", "pmh", "premarket", "onpiyasa"),
    "prev_close": ("pc", "prevclose", "prev", "onceki", "önceki", "kapanis", "kapanış"),
    "volume": ("vol", "hacim", "v"),
    "avg_volume": ("avgvol", "avg", "ortalama", "ortalamahacim", "ohacim"),
    "float_shares": ("float", "flt", "dolasim", "dolaşım"),
    "short_float": ("short", "shortfloat", "shortoran", "si"),
}
CATALYST_KEYS = ("haber", "katalizor", "katalizör", "news", "catalyst")

_KEY_LOOKUP = {alias: name for name, aliases in ALIASES.items() for alias in aliases}

_NUMERIC_VALUE = r"[\$%]{0,2}[+-]?\d+(?:[.,]\d+)?\s*(?:mln|mn|bn|[kmbKMB])?\s*%?"
_KV_RE = re.compile(
    r"(?<![^\s(])(" + "|".join(sorted(_KEY_LOOKUP, key=len, reverse=True)) + r")"
    r"\s*[=:]\s*(" + _NUMERIC_VALUE + r")",
    re.IGNORECASE,
)
_CATALYST_KV_RE = re.compile(
    r"(?<![^\s(])(" + "|".join(CATALYST_KEYS) + r")\s*[=:]\s*(.+)$",
    re.IGNORECASE | re.DOTALL,
)
_TICKER_RE = re.compile(r"^\$?([A-Za-z]{1,6}(?:[.\-][A-Za-z]{1,2})?)$")
_NUMBER_TOKEN_RE = re.compile(
    r"^[\$%]{0,2}[+-]?\d+(?:[.,]\d+)?\s*(?:mln|mn|bn|[kmbKMB])?%?$", re.IGNORECASE
)


class ParseError(ValueError):
    """Girdi çözümlenemediğinde atılır; mesajı kullanıcıya gösterilebilir."""


@dataclass
class ParsedInput:
    """Çözümlenmiş girdi. Fiyat yoksa canlı veriyle tamamlanabilir."""

    ticker: str
    fields: dict[str, Any] = field(default_factory=dict)

    @property
    def has_price(self) -> bool:
        return self.fields.get("price") is not None

    def to_quote(self, source: str = "manuel") -> Quote:
        if not self.has_price:
            raise ParseError(
                f"${self.ticker} için fiyat verilmedi ve canlı veri alınamadı.\n\n{USAGE}"
            )
        data = dict(self.fields)
        price = data.pop("price")
        return Quote(ticker=self.ticker, price=price, source=source, **data)


def parse_fields(text: str) -> ParsedInput:
    """Metni hisse kodu + alan sözlüğüne ayrıştırır (fiyat zorunlu değil)."""
    raw = (text or "").strip()
    if not raw:
        raise ParseError(f"Girdi boş.\n\n{USAGE}")

    fields: dict[str, Any] = {}
    catalyst: Optional[str] = None

    match = _CATALYST_KV_RE.search(raw)
    if match:
        catalyst = match.group(2).strip().strip('"').strip()
        raw = (raw[: match.start()] + " " + raw[match.end() :]).strip()

    def _take_kv(m: re.Match) -> str:
        name = _KEY_LOOKUP[m.group(1).lower()]
        try:
            fields[name] = parse_number(m.group(2))
        except ValueError as exc:
            raise ParseError(f"{m.group(1)} değeri okunamadı: {m.group(2)!r}") from exc
        return " "

    raw = _KV_RE.sub(_take_kv, raw).strip()

    tokens = raw.split()
    if not tokens:
        raise ParseError(f"Hisse kodu bulunamadı.\n\n{USAGE}")

    ticker_match = _TICKER_RE.match(tokens[0])
    if not ticker_match:
        raise ParseError(
            f"'{tokens[0]}' geçerli bir hisse kodu değil (ör. RKLB veya $RKLB).\n\n{USAGE}"
        )
    ticker = ticker_match.group(1).upper()

    index = 1
    while index < len(tokens):
        token = tokens[index]
        if not _NUMBER_TOKEN_RE.match(token):
            break
        try:
            value = parse_number(token)
        except ValueError:
            break
        is_pct = "%" in token or token.lstrip("$")[:1] in ("+", "-")
        target = "change_pct" if is_pct else "price"
        if fields.get(target) is not None:
            break
        fields[target] = value
        index += 1

    trailing = " ".join(tokens[index:]).strip()
    if catalyst is None and trailing:
        catalyst = trailing
    if catalyst:
        fields["catalyst"] = catalyst

    return ParsedInput(ticker=ticker, fields=fields)


def parse_input(text: str, source: str = "manuel") -> Quote:
    """Metni doğrudan `Quote` nesnesine çevirir (fiyat zorunlu)."""
    parsed = parse_fields(text)
    try:
        return parsed.to_quote(source=source)
    except ValueError as exc:
        if isinstance(exc, ParseError):
            raise
        raise ParseError(str(exc)) from exc
