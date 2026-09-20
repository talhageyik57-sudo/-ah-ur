"""app modülü: Telegram handler davranışı (ağ erişimi olmadan)."""

import unittest
from types import SimpleNamespace
from unittest import mock

try:
    from smallcap import app
except ImportError:  # python-telegram-bot kurulu değilse testler atlanır
    app = None

from smallcap.config import Settings


def _fake_update(text: str, chat_type: str = "private", chat_id: int = 42):
    message = SimpleNamespace(text=text, reply_text=mock.AsyncMock())
    return SimpleNamespace(
        effective_message=message,
        effective_chat=SimpleNamespace(id=chat_id, type=chat_type),
    )


def _fake_context(settings: Settings, args=None, bot_data=None):
    return SimpleNamespace(
        application=SimpleNamespace(bot_data=bot_data if bot_data is not None else {"settings": settings}),
        bot=SimpleNamespace(send_chat_action=mock.AsyncMock(), send_message=mock.AsyncMock()),
        args=args or [],
    )


def _fake_callback(data: str, chat_id: int = 42):
    query = SimpleNamespace(
        data=data,
        message=SimpleNamespace(chat=SimpleNamespace(id=chat_id)),
        answer=mock.AsyncMock(),
        edit_message_reply_markup=mock.AsyncMock(),
    )
    return SimpleNamespace(callback_query=query)


BROADCAST = Settings(
    parse_mode="html",
    auto_fetch=False,
    target_chat_id="-1001234567890",
    allowed_chat_ids=frozenset({42}),
)


@unittest.skipIf(app is None, "python-telegram-bot kurulu değil")
class HandlerTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.settings = Settings(parse_mode="html", auto_fetch=False)

    def _sent(self, update):
        update.effective_message.reply_text.assert_awaited()
        return update.effective_message.reply_text.await_args.args[0]

    async def test_analiz_command_produces_post(self):
        update = _fake_update("/analiz RKLB 4.25 %32 haber")
        context = _fake_context(self.settings, args=["RKLB", "4.25", "%32", "haber"])
        await app.cmd_analiz(update, context)
        body = self._sent(update)
        self.assertIn("US SMALL-CAP", body)
        self.assertIn("<b>", body)

    async def test_plain_message_in_private_chat(self):
        update = _fake_update("RKLB 4.25 %32 haber")
        await app.on_message(update, _fake_context(self.settings))
        self.assertIn("$RKLB", self._sent(update))

    async def test_group_message_without_dollar_is_ignored(self):
        update = _fake_update("bugün hava güzel", chat_type="supergroup")
        await app.on_message(update, _fake_context(self.settings))
        update.effective_message.reply_text.assert_not_awaited()

    async def test_group_message_with_dollar_is_handled(self):
        update = _fake_update("$RKLB 4.25 %32 haber", chat_type="supergroup")
        await app.on_message(update, _fake_context(self.settings))
        self.assertIn("$RKLB", self._sent(update))

    async def test_parse_error_is_reported_to_user(self):
        update = _fake_update("12345 not a ticker")
        await app.on_message(update, _fake_context(self.settings))
        self.assertIn("⚠️", self._sent(update))

    async def test_unauthorized_chat_is_rejected(self):
        settings = Settings(parse_mode="html", auto_fetch=False, allowed_chat_ids=frozenset({99}))
        update = _fake_update("RKLB 4.25 %32", chat_id=42)
        await app.on_message(update, _fake_context(settings))
        self.assertIn("yetkili listesinde değil", self._sent(update))

    async def test_allowed_chat_passes(self):
        settings = Settings(parse_mode="html", auto_fetch=False, allowed_chat_ids=frozenset({42}))
        update = _fake_update("RKLB 4.25 %32", chat_id=42)
        await app.on_message(update, _fake_context(settings))
        self.assertIn("US SMALL-CAP", self._sent(update))

    async def test_start_shows_usage(self):
        update = _fake_update("/start")
        await app.cmd_start(update, _fake_context(self.settings))
        self.assertIn("Girdi biçimi", self._sent(update))

    async def test_ornek_command(self):
        update = _fake_update("/ornek")
        await app.cmd_ornek(update, _fake_context(self.settings))
        self.assertIn("US SMALL-CAP", self._sent(update))

    async def test_detay_command(self):
        update = _fake_update("/detay RKLB 4.25 %32")
        context = _fake_context(self.settings, args=["RKLB", "4.25", "%32"])
        await app.cmd_detay(update, context)
        self.assertIn("HESAP NOTU", self._sent(update))

    async def test_unexpected_error_is_contained(self):
        update = _fake_update("RKLB 4.25 %32")
        with mock.patch.object(app, "analyze", side_effect=RuntimeError("boom")):
            with self.assertLogs(app.logger, level="ERROR"):
                await app.on_message(update, _fake_context(self.settings))
        self.assertIn("beklenmeyen bir hata", self._sent(update))


@unittest.skipIf(app is None, "python-telegram-bot kurulu değil")
class BuildApplicationTest(unittest.TestCase):
    def test_requires_token(self):
        with self.assertRaises(RuntimeError):
            app.build_application(Settings(bot_token=None))

    def test_rejects_bad_parse_mode(self):
        with self.assertRaises(RuntimeError):
            app.build_application(Settings(bot_token="1:AA", parse_mode="wingdings"))

    def test_custom_api_base_url_is_applied(self):
        application = app.build_application(
            Settings(bot_token="1:AA", api_base_url="http://127.0.0.1:8099/bot")
        )
        self.assertTrue(application.bot.base_url.startswith("http://127.0.0.1:8099/bot"))

    def test_default_api_base_url_is_telegram(self):
        application = app.build_application(Settings(bot_token="1:AA"))
        self.assertTrue(application.bot.base_url.startswith("https://api.telegram.org/bot"))

    def test_builds_with_token(self):
        application = app.build_application(Settings(bot_token="1:AA", parse_mode="html"))
        self.assertEqual(application.bot_data["settings"].parse_mode, "html")
        self.assertTrue(sum(len(v) for v in application.handlers.values()) >= 5)


if __name__ == "__main__":
    unittest.main()


@unittest.skipIf(app is None, "python-telegram-bot kurulu değil")
class StartupErrorTest(unittest.TestCase):
    """Başlatma hataları kullanıcıya ham traceback olarak gitmemeli."""

    def _run_main_with(self, error):
        from telegram.error import InvalidToken, NetworkError  # noqa: F401

        fake = mock.MagicMock()
        fake.run_polling.side_effect = error
        with mock.patch.object(app, "build_application", return_value=fake), mock.patch.object(
            app.Settings, "from_env", return_value=Settings(bot_token="1:AA")
        ):
            with self.assertRaises(RuntimeError) as ctx:
                app.main()
        return str(ctx.exception)

    def test_invalid_token_is_explained(self):
        from telegram.error import InvalidToken

        message = self._run_main_with(InvalidToken("bad token"))
        self.assertIn("BotFather", message)

    def test_network_error_is_explained(self):
        from telegram.error import NetworkError

        message = self._run_main_with(NetworkError("proxy 403"))
        self.assertIn("api.telegram.org", message)
        self.assertIn("proxy 403", message)


@unittest.skipIf(app is None, "python-telegram-bot kurulu değil")
class BroadcastButtonTest(unittest.IsolatedAsyncioTestCase):
    """Analiz altındaki '📢 Kanala Gönder' butonu."""

    async def test_button_absent_without_target(self):
        settings = Settings(parse_mode="html", auto_fetch=False)
        update = _fake_update("RKLB 4.25 %32")
        await app.on_message(update, _fake_context(settings))
        kwargs = update.effective_message.reply_text.await_args.kwargs
        self.assertIsNone(kwargs.get("reply_markup"))

    async def test_button_absent_for_unlisted_user(self):
        update = _fake_update("RKLB 4.25 %32", chat_id=43)
        await app.on_message(update, _fake_context(BROADCAST))
        # Yetkisiz sohbete zaten analiz de verilmez.
        self.assertIn("yetkili listesinde değil", update.effective_message.reply_text.await_args.args[0])

    async def test_button_present_for_authorized_user(self):
        update = _fake_update("RKLB 4.25 %32", chat_id=42)
        await app.on_message(update, _fake_context(BROADCAST))
        kwargs = update.effective_message.reply_text.await_args.kwargs
        self.assertIsNotNone(kwargs.get("reply_markup"))

    async def test_button_absent_on_details(self):
        update = _fake_update("/detay RKLB 4.25 %32", chat_id=42)
        context = _fake_context(BROADCAST, args=["RKLB", "4.25", "%32"])
        await app.cmd_detay(update, context)
        self.assertIsNone(update.effective_message.reply_text.await_args.kwargs.get("reply_markup"))


@unittest.skipIf(app is None, "python-telegram-bot kurulu değil")
class BroadcastCallbackTest(unittest.IsolatedAsyncioTestCase):
    async def _produce_then_press(self, send_message=None):
        """Önce analiz üretir, sonra butonuna basar; aynı bot_data paylaşılır."""
        bot_data = {"settings": BROADCAST}
        update = _fake_update("RKLB 4.25 %32", chat_id=42)
        context = _fake_context(BROADCAST, bot_data=bot_data)
        await app.on_message(update, context)
        markup = update.effective_message.reply_text.await_args.kwargs["reply_markup"]
        data = markup.inline_keyboard[0][0].callback_data

        press = _fake_callback(data)
        press_context = _fake_context(BROADCAST, bot_data=bot_data)
        if send_message is not None:
            press_context.bot.send_message = send_message
        await app.on_send_callback(press, press_context)
        return press, press_context

    async def test_press_sends_to_target_channel(self):
        press, context = await self._produce_then_press()
        context.bot.send_message.assert_awaited_once()
        kwargs = context.bot.send_message.await_args.kwargs
        self.assertEqual(kwargs["chat_id"], -1001234567890, "sayısal kanal ID int olmalı")
        self.assertIn("US SMALL-CAP", kwargs["text"])
        press.callback_query.edit_message_reply_markup.assert_awaited_once()

    async def test_failed_send_keeps_button(self):
        from telegram.error import TelegramError

        failing = mock.AsyncMock(side_effect=TelegramError("bot kanalda yönetici değil"))
        with self.assertLogs(app.logger, level="WARNING"):
            press, _ = await self._produce_then_press(send_message=failing)
        press.callback_query.edit_message_reply_markup.assert_not_awaited()
        alert = press.callback_query.answer.await_args.args[0]
        self.assertIn("yönetici değil", alert)

    async def test_expired_key_is_reported(self):
        press = _fake_callback("send:yokboylebirsey")
        await app.on_send_callback(press, _fake_context(BROADCAST))
        press.callback_query.answer.assert_awaited()
        self.assertIn("tekrar üretin", press.callback_query.answer.await_args.args[0])

    async def test_unauthorized_press_is_blocked(self):
        press = _fake_callback("send:abc", chat_id=999)
        context = _fake_context(BROADCAST)
        await app.on_send_callback(press, context)
        context.bot.send_message.assert_not_awaited()

    async def test_pending_store_is_capped(self):
        bot_data = {"settings": BROADCAST}
        context = _fake_context(BROADCAST, bot_data=bot_data)
        for index in range(app.MAX_PENDING + 10):
            app._remember(context, f"gönderi {index}")
        self.assertEqual(len(bot_data["pending_posts"]), app.MAX_PENDING)


@unittest.skipIf(app is None, "python-telegram-bot kurulu değil")
class GonderCommandTest(unittest.IsolatedAsyncioTestCase):
    async def test_sends_directly_to_channel(self):
        update = _fake_update("/gonder RKLB 4.25 %32", chat_id=42)
        context = _fake_context(BROADCAST, args=["RKLB", "4.25", "%32"])
        await app.cmd_gonder(update, context)
        context.bot.send_message.assert_awaited_once()
        self.assertIn("kanala iletildi", update.effective_message.reply_text.await_args.args[0])

    async def test_refuses_without_target(self):
        settings = Settings(parse_mode="html", auto_fetch=False, allowed_chat_ids=frozenset({42}))
        update = _fake_update("/gonder RKLB 4.25 %32", chat_id=42)
        context = _fake_context(settings, args=["RKLB", "4.25", "%32"])
        await app.cmd_gonder(update, context)
        context.bot.send_message.assert_not_awaited()
        self.assertIn("TELEGRAM_TARGET_CHAT_ID", update.effective_message.reply_text.await_args.args[0])

    async def test_refuses_open_bot(self):
        settings = Settings(parse_mode="html", auto_fetch=False, target_chat_id="-100123")
        update = _fake_update("/gonder RKLB 4.25 %32", chat_id=42)
        context = _fake_context(settings, args=["RKLB", "4.25", "%32"])
        await app.cmd_gonder(update, context)
        context.bot.send_message.assert_not_awaited()
        self.assertIn("yetkili kullanıcı listesi", update.effective_message.reply_text.await_args.args[0])

    async def test_reports_send_failure(self):
        from telegram.error import TelegramError

        update = _fake_update("/gonder RKLB 4.25 %32", chat_id=42)
        context = _fake_context(BROADCAST, args=["RKLB", "4.25", "%32"])
        context.bot.send_message = mock.AsyncMock(side_effect=TelegramError("chat not found"))
        with self.assertLogs(app.logger, level="WARNING"):
            await app.cmd_gonder(update, context)
        self.assertIn("chat not found", update.effective_message.reply_text.await_args.args[0])

    async def test_parse_error_does_not_reach_channel(self):
        update = _fake_update("/gonder 12345", chat_id=42)
        context = _fake_context(BROADCAST, args=["12345"])
        await app.cmd_gonder(update, context)
        context.bot.send_message.assert_not_awaited()
        self.assertIn("⚠️", update.effective_message.reply_text.await_args.args[0])
