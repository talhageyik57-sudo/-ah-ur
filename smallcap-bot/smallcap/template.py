"""Telegram gönderi şablonu ve render fonksiyonları.

Şablon metni birebir sabittir — değişkenler yalnızca köşeli parantezli
alanların yerine geçer. Çıktı doğrudan kopyalanıp Telegram'a atılabilir.
"""

from __future__ import annotations

from typing import Optional

from . import markup
from .levels import compute_levels
from .models import Levels, Quote
from .numbers import fmt_pct, fmt_price

DEFAULT_CATALYST = "Ani Hacim Patlaması / Squeeze"

POST_TEMPLATE = """🇺🇸 🚀 **US SMALL-CAP | HACİMLİ MUM & HEDEF BÖLGELERİ** 🚀

📌 **Ticker:** ${ticker}
💰 **Son Fiyat:** ${price}{change}
⚡ **Katalizör / Haber:** {catalyst}

───────────────────

🎯 **TEKNİK SEVİYELER VE AKSİYON PLANI:**

🔴 **İlk Direnç:** ${resistance}
🟢 **İlk Destek:** ${support}

🔥 **KIRILIM & ALIM STRATEJİSİ:**
└ **${resistance}** seviyesi üzeri **hacimli ilk mum kapanışı (5dk / 15dk)** geldiğinde breakout doğrulanmış olur.
└ Hacimli ilk mum gövdesi direncin üstünde kalırsa **${breakout}** seviyelerinden kademeli alım düşünülebilir. *(Retest yaparsa daha güvenli giriş fırsatıdır).*

🎯 **HEDEF SEVİYELERİ (KAR AL / TP):**
🎯 **Hedef 1 (TP1):** ${tp1} *(Kısa vadeli kar al / Maliyet sıfırlama bölgesi)*
🚀 **Hedef 2 (TP2):** ${tp2} *(Ana direnç / Squeeze devamı halinde nihai hedef)*

🛑 **STOP-LOSS (RİSK ÇIKIŞI):**
└ **${stop}** altı sarkmalarda ve mum kapanışlarında stop olunmalıdır.
└ *İlk Destek olan **${support}** seviyesinin kırılması durumunda pozisyonda zorlamadan riski sıfırlamak kritik!*

💡 **HIZLI TÜYO:**
• Hacimsiz kırılımlara (Fake-out) atlama, mutlaka **ortalamanın üzerinde hacimle gelen ilk yeşil mumu** bekle! Hedef 1'e ulaştığında en azından kârın bir kısmını cebine koymayı unutma.

⚠️ *Not: Small-Cap piyasalarda slippage ve oynaklık yüksektir. Şablon sadece takip amaçlıdır, kendi risk yönetiminizi uygulayınız.*"""


def build_catalyst(quote: Quote) -> str:
    """Katalizör satırı: haber varsa haber, yoksa hacim/squeeze notu."""
    text = quote.catalyst or DEFAULT_CATALYST
    extras = []
    rvol = quote.rvol
    if rvol and rvol >= 2:
        extras.append(f"RVOL ~{rvol:.1f}x")
    if quote.is_squeeze_candidate:
        extras.append("düşük float + yüksek short → squeeze adayı")
    if extras:
        text = f"{text} ({' • '.join(extras)})"
    return text


def render_post(
    quote: Quote,
    levels: Optional[Levels] = None,
    parse_mode: str = "plain",
) -> str:
    """Gönderinin tam metnini üretir.

    `parse_mode`: "plain" (kanonik markdown çıktısı sökülmüş), "html" veya
    "markdownv2". Telegram'a gönderirken HTML önerilir.
    """
    levels = levels or compute_levels(quote)
    change = f" ({fmt_pct(quote.change_pct)})" if quote.change_pct is not None else ""

    text = POST_TEMPLATE.format(
        ticker=quote.ticker,
        price=fmt_price(quote.price),
        change=change,
        catalyst=build_catalyst(quote),
        resistance=fmt_price(levels.resistance),
        support=fmt_price(levels.support),
        breakout=fmt_price(levels.breakout_entry),
        tp1=fmt_price(levels.tp1),
        tp2=fmt_price(levels.tp2),
        stop=fmt_price(levels.stop),
    )
    return markup.convert(text, parse_mode)


def render_details(quote: Quote, levels: Optional[Levels] = None, parse_mode: str = "plain") -> str:
    """Hesap gerekçeleri + risk/ödül tablosu (gönderi değil, kontrol çıktısı)."""
    levels = levels or compute_levels(quote)
    lines = [
        f"🧮 **${quote.ticker} — HESAP NOTU**",
        "",
        f"`{quote.summary()}`",
        "",
        f"• Direnç: **${fmt_price(levels.resistance)}**  •  Destek: **${fmt_price(levels.support)}**",
        f"• Giriş: **${fmt_price(levels.breakout_entry)}**  •  Stop: **${fmt_price(levels.stop)}**",
        f"• Birim risk: **${fmt_price(levels.risk)}** (giriş - stop)",
    ]
    if levels.rr_tp1 and levels.rr_tp2:
        lines.append(
            f"• R/R — TP1: **{levels.rr_tp1:.2f}R**  •  TP2: **{levels.rr_tp2:.2f}R**"
        )
    if levels.assumptions:
        lines.append("")
        lines.append("**Varsayımlar:**")
        lines.extend(f"└ {note}" for note in levels.assumptions)
    return markup.convert("\n".join(lines), parse_mode)
