"""Telegram bot katmanı (python-telegram-bot v21).

Komutlar:
    /start, /yardim   kullanım bilgisi
    /analiz <girdi>   gönderiyi üretir
    /detay  <girdi>   seviyelerin hesap gerekçesini ve R/R oranını gösterir
    /ornek            örnek bir gönderi üretir

Özel sohbette komutsuz mesajlar da analiz olarak işlenir. Gruplarda
gürültü yapmamak için yalnızca komutlara ve `$TICKER ...` ile başlayan
mesajlara yanıt verilir.
"""

from __future__ import annotations

import logging
from typing import Optional

from telegram import BotCommand, Update
from telegram.constants import ParseMode
from telegram.error import InvalidToken, NetworkError
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import markup
from .config import Settings
from .parser import USAGE, ParseError
from .service import analyze, analyze_details

logger = logging.getLogger(__name__)

ORNEK_GIRDI = "RKLB 4.25 %32 Uydu sözleşmesi haberi hod=4.48 lod=3.10 vol=48M avgvol=6M"

WELCOME = (
    "🇺🇸 **US Small-Cap Breakout Botu**\n\n"
    "Hisse verisini yaz, Telegram'a hazır **Hacimli Mum & Breakout Notu** üreteyim.\n\n"
    "**Girdi biçimi:**\n"
    "`<HİSSE> <FİYAT> <%DEĞİŞİM> <haber metni>`\n\n"
    "**Örnek:**\n"
    "`RKLB 4.25 %32 FDA onayı sonrası hacim patlaması`\n\n"
    "**Seviyeleri keskinleştiren ek alanlar:**\n"
    "`hod=` gün içi tepe  •  `lod=` gün içi dip  •  `pm=` pre-market tepesi\n"
    "`vol=` hacim  •  `avgvol=` ortalama hacim  •  `float=` float  •  `short=` short oranı\n"
    "`haber=` katalizör metni\n\n"
    "**Tam örnek:**\n"
    "`$ABCD 0.4523 +118% hod=0.52 lod=0.31 float=14M short=%24 haber=Ortaklık duyurusu`\n\n"
    "**Komutlar:** /analiz  •  /detay  •  /ornek  •  /yardim"
)

_PARSE_MODES = {
    "html": ParseMode.HTML,
    "markdownv2": ParseMode.MARKDOWN_V2,
    "markdown_v2": ParseMode.MARKDOWN_V2,
    "plain": None,
    "none": None,
    "text": None,
}


def _settings(context: ContextTypes.DEFAULT_TYPE) -> Settings:
    return context.application.bot_data.get("settings") or Settings()


async def _send(update: Update, text: str, settings: Settings, convert: bool = True) -> None:
    """Metni ayarlanan parse_mode ile gönderir."""
    body = markup.convert(text, settings.parse_mode) if convert else text
    await update.effective_message.reply_text(
        body,
        parse_mode=_PARSE_MODES.get(settings.parse_mode, ParseMode.HTML),
        disable_web_page_preview=True,
    )


def _authorized(update: Update, settings: Settings) -> bool:
    chat = update.effective_chat
    return settings.is_allowed(chat.id if chat else None)


async def _run(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, details: bool) -> None:
    settings = _settings(context)
    if not _authorized(update, settings):
        await _send(update, "⛔️ Bu sohbet yetkili listesinde değil.", settings)
        return
    if not text.strip():
        await _send(update, f"Girdi bekleniyor.\n\n`{USAGE}`", settings)
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    try:
        runner = analyze_details if details else analyze
        # Gönderi metni zaten hedef biçime çevrilmiş halde döner.
        output = runner(text, settings, settings.parse_mode)
    except ParseError as exc:
        await _send(update, f"⚠️ {exc}", settings)
        return
    except Exception:  # beklenmeyen hata kullanıcıya ham traceback olarak gitmemeli
        logger.exception("analiz başarısız: %r", text)
        await _send(update, "⚠️ Analiz sırasında beklenmeyen bir hata oluştu.", settings)
        return

    await _send(update, output, settings, convert=False)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _send(update, WELCOME, _settings(context))


async def cmd_analiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run(update, context, " ".join(context.args or []), details=False)


async def cmd_detay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run(update, context, " ".join(context.args or []), details=True)


async def cmd_ornek(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _run(update, context, ORNEK_GIRDI, details=False)


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.effective_message
    chat = update.effective_chat
    text = (message.text or "").strip()
    if not text:
        return
    # Gruplarda yalnızca açık bir hisse girdisine yanıt ver.
    if chat and chat.type != "private" and not text.startswith("$"):
        return
    await _run(update, context, text, details=False)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.exception("işlenmemiş hata", exc_info=context.error)


async def _post_init(application: Application) -> None:
    await application.bot.set_my_commands(
        [
            BotCommand("analiz", "Hisse verisinden breakout gönderisi üret"),
            BotCommand("detay", "Seviyelerin hesap gerekçesi ve R/R oranı"),
            BotCommand("ornek", "Örnek gönderi"),
            BotCommand("yardim", "Kullanım bilgisi"),
        ]
    )


def build_application(settings: Optional[Settings] = None) -> Application:
    """Handler'ları bağlanmış Telegram uygulamasını kurar."""
    settings = settings or Settings.from_env()
    if not settings.bot_token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN tanımlı değil. .env dosyasını oluşturun "
            "(.env.example dosyasını kopyalayabilirsiniz)."
        )
    if settings.parse_mode not in _PARSE_MODES:
        raise RuntimeError(f"Geçersiz TELEGRAM_PARSE_MODE: {settings.parse_mode}")

    application = Application.builder().token(settings.bot_token).post_init(_post_init).build()
    application.bot_data["settings"] = settings

    application.add_handler(CommandHandler(["start", "yardim", "help"], cmd_start))
    application.add_handler(CommandHandler("analiz", cmd_analiz))
    application.add_handler(CommandHandler("detay", cmd_detay))
    application.add_handler(CommandHandler("ornek", cmd_ornek))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    application.add_error_handler(on_error)
    return application


def main() -> None:
    settings = Settings.from_env()
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    application = build_application(settings)
    logger.info(
        "Bot başlatılıyor (parse_mode=%s, canlı veri=%s)", settings.parse_mode, settings.auto_fetch
    )
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except InvalidToken as exc:
        # Ham traceback yerine ne yapılacağını söyleyen mesaj göster.
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN geçersiz. BotFather'da /mybots > API Token "
            "adımından token'ı yeniden alıp .env dosyasına yazın."
        ) from exc
    except NetworkError as exc:
        raise RuntimeError(
            "Telegram API'sine ulaşılamadı. İnternet bağlantısını, proxy/güvenlik "
            "duvarı ayarlarını ve api.telegram.org erişimini kontrol edin.\n"
            f"Ayrıntı: {exc}"
        ) from exc


if __name__ == "__main__":
    main()
