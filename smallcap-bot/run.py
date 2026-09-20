#!/usr/bin/env python3
"""Botu başlatan giriş noktası: `python3 run.py`."""

from __future__ import annotations

import sys


def main() -> int:
    try:
        from smallcap.app import main as run_bot
    except ImportError as exc:  # telegram kurulu değilse anlaşılır mesaj ver
        print(
            "Telegram kütüphanesi bulunamadı.\n"
            "Kurulum: pip install -r requirements.txt\n"
            f"Ayrıntı: {exc}",
            file=sys.stderr,
        )
        return 1

    try:
        run_bot()
    except RuntimeError as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nBot durduruldu.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
