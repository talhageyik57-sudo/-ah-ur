"""Terminalden analiz üretmek için komut satırı arayüzü.

    python3 -m smallcap.cli "RKLB 4.25 %32 FDA onayı"
    python3 -m smallcap.cli --detay --format html "SOUN 12.40 -3.2"
"""

from __future__ import annotations

import argparse
import logging
import sys

from .config import Settings
from .parser import USAGE, ParseError
from .service import analyze, analyze_details


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="smallcap",
        description="US Small-Cap breakout gönderisi üretir.",
        epilog=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("girdi", nargs="+", help="Hisse kodu, fiyat, değişim ve haber")
    parser.add_argument(
        "--format",
        dest="parse_mode",
        default="plain",
        choices=("plain", "html", "markdownv2"),
        help="Çıktı biçimi (varsayılan: plain)",
    )
    parser.add_argument(
        "--detay",
        action="store_true",
        help="Gönderi yerine hesap gerekçelerini ve R/R oranını yazar",
    )
    parser.add_argument(
        "--canli",
        action="store_true",
        help="Eksik alanları canlı veri sağlayıcısından tamamlamayı dene",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")
    settings = Settings.from_env()
    settings.auto_fetch = args.canli

    text = " ".join(args.girdi)
    try:
        output = (analyze_details if args.detay else analyze)(text, settings, args.parse_mode)
    except ParseError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
