"""Şablon işaretlemesini Telegram'ın anladığı biçimlere çevirir.

Şablon kanonik olarak Markdown benzeri yazılır (`**kalın**`, `*italik*`,
`` `kod` ``). Telegram bu sözdizimini doğrudan kabul etmez: HTML modunda
`<b>`, MarkdownV2 modunda `*...*` ve kaçışlı özel karakterler gerekir.
Metin önce düğümlere ayrıştırılır, sonra hedef biçime göre yazılır — bu
sayede kaçış işlemi işaretleme karakterlerini bozmaz.
"""

from __future__ import annotations

import html
import re
from typing import Iterable, Union

Node = Union[str, tuple]  # ("bold"|"italic"|"code", içerik)

_CODE_RE = re.compile(r"`([^`\n]+)`")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
# İtalik gövdesi kalın parçalar içerebilir: *... **X** ...*
_ITALIC_RE = re.compile(r"(?<!\*)\*(?!\*)((?:[^*\n]|\*\*)+?)(?<!\*)\*(?!\*)")

# MarkdownV2'de kaçışı zorunlu olan karakterler (Telegram Bot API).
_MDV2_SPECIAL = set(r"_*[]()~`>#+-=|{}.!\\")


def parse(text: str) -> list[Node]:
    """Kanonik metni düğüm listesine ayrıştırır."""
    return _parse_segment(text)


_PATTERNS = (
    ("code", _CODE_RE, False),
    ("bold", _BOLD_RE, True),
    ("italic", _ITALIC_RE, True),
)


def _parse_segment(text: str) -> list[Node]:
    if not text:
        return []

    # Metinde en erken başlayan işaretleme kazanır; böylece içine kalın
    # gömülmüş bir italik blok (`*... **X** ...*`) parçalanmadan okunur.
    best = None
    for kind, pattern, recurse in _PATTERNS:
        match = pattern.search(text)
        if match and (best is None or match.start() < best[0].start()):
            best = (match, kind, recurse)

    if best is None:
        return [text]

    match, kind, recurse = best
    inner = match.group(1)
    child = _parse_segment(inner) if recurse else [inner]
    return (
        _parse_segment(text[: match.start()])
        + [(kind, child)]
        + _parse_segment(text[match.end() :])
    )


def to_html(text: str) -> str:
    """Telegram `parse_mode=HTML` çıktısı."""
    return _render(parse(text), _html_text, _html_wrap)


def to_markdown_v2(text: str) -> str:
    """Telegram `parse_mode=MarkdownV2` çıktısı."""
    return _render(parse(text), _mdv2_text, _mdv2_wrap)


def to_plain(text: str) -> str:
    """İşaretlemesi sökülmüş düz metin (CLI / log / test için)."""
    return _render(parse(text), lambda s: s, lambda kind, body: body)


def _render(nodes: Iterable[Node], text_fn, wrap_fn) -> str:
    out = []
    for node in nodes:
        if isinstance(node, str):
            out.append(text_fn(node))
        else:
            kind, children = node
            if kind == "code":
                out.append(wrap_fn(kind, children[0]))
            else:
                out.append(wrap_fn(kind, _render(children, text_fn, wrap_fn)))
    return "".join(out)


def _html_text(text: str) -> str:
    return html.escape(text, quote=False)


def _html_wrap(kind: str, body: str) -> str:
    if kind == "bold":
        return f"<b>{body}</b>"
    if kind == "italic":
        return f"<i>{body}</i>"
    return f"<code>{html.escape(body, quote=False)}</code>"


def _mdv2_text(text: str) -> str:
    return "".join("\\" + ch if ch in _MDV2_SPECIAL else ch for ch in text)


def _mdv2_wrap(kind: str, body: str) -> str:
    if kind == "bold":
        return f"*{body}*"
    if kind == "italic":
        return f"_{body}_"
    escaped = body.replace("\\", "\\\\").replace("`", "\\`")
    return f"`{escaped}`"


def convert(text: str, parse_mode: str) -> str:
    """`parse_mode` adına göre uygun dönüştürücüyü uygular."""
    mode = (parse_mode or "").strip().lower()
    if mode in ("html", ""):
        return to_html(text)
    if mode in ("markdownv2", "markdown_v2", "md2"):
        return to_markdown_v2(text)
    if mode in ("plain", "none", "text"):
        return to_plain(text)
    raise ValueError(f"desteklenmeyen parse_mode: {parse_mode}")
