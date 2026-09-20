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


def _fake_context(settings: Settings, args=None):
    return SimpleNamespace(
        application=SimpleNamespace(bot_data={"settings": settings}),
        bot=SimpleNamespace(send_chat_action=mock.AsyncMock()),
        args=args or [],
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

    def test_builds_with_token(self):
        application = app.build_application(Settings(bot_token="1:AA", parse_mode="html"))
        self.assertEqual(application.bot_data["settings"].parse_mode, "html")
        self.assertTrue(sum(len(v) for v in application.handlers.values()) >= 5)


if __name__ == "__main__":
    unittest.main()
