"""config modülü: ortam değişkeni okuma ve yetki kuralları."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from smallcap.config import Settings, load_dotenv


class DotenvTest(unittest.TestCase):
    def test_reads_file_without_overriding_environment(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env"
            path.write_text(
                "# yorum\nTELEGRAM_BOT_TOKEN=abc\nTELEGRAM_PARSE_MODE='html'\nBOS=\n",
                encoding="utf-8",
            )
            with mock.patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "önceden-var"}, clear=False):
                loaded = load_dotenv(path)
                self.assertEqual(loaded["TELEGRAM_PARSE_MODE"], "html")
                self.assertEqual(os.environ["TELEGRAM_BOT_TOKEN"], "önceden-var")

    def test_missing_file_is_silent(self):
        self.assertEqual(load_dotenv("/yok/boyle/bir/.env"), {})


class FromEnvTest(unittest.TestCase):
    ENV = {
        "TELEGRAM_BOT_TOKEN": "1:AA",
        "TELEGRAM_PARSE_MODE": "HTML",
        "TELEGRAM_ALLOWED_CHAT_IDS": "5418325557, -1001234567890 ;kötü",
        "TELEGRAM_TARGET_CHAT_ID": "-1001234567890",
        "AUTO_FETCH": "hayır",
    }

    def test_parses_all_fields(self):
        with mock.patch.dict(os.environ, self.ENV, clear=False):
            settings = Settings.from_env("/yok/boyle/bir/.env")
        self.assertEqual(settings.bot_token, "1:AA")
        self.assertEqual(settings.parse_mode, "html")
        self.assertEqual(settings.allowed_chat_ids, frozenset({5418325557, -1001234567890}))
        self.assertEqual(settings.target_chat_id, "-1001234567890")
        self.assertFalse(settings.auto_fetch, "AUTO_FETCH=hayır kapalı demek")


class AuthorizationTest(unittest.TestCase):
    def test_empty_whitelist_allows_everyone(self):
        self.assertTrue(Settings().is_allowed(42))

    def test_whitelist_restricts(self):
        settings = Settings(allowed_chat_ids=frozenset({42}))
        self.assertTrue(settings.is_allowed(42))
        self.assertFalse(settings.is_allowed(43))
        self.assertFalse(settings.is_allowed(None))


class BroadcastAuthorizationTest(unittest.TestCase):
    """Kanala gönderim hedef + beyaz liste birlikte tanımlıysa açılır."""

    def test_requires_target_and_whitelist(self):
        self.assertFalse(Settings().can_broadcast(42))
        self.assertFalse(Settings(target_chat_id="-100123").can_broadcast(42))
        self.assertFalse(Settings(allowed_chat_ids=frozenset({42})).can_broadcast(42))

    def test_open_bot_cannot_broadcast(self):
        # Beyaz liste boşken botu bulan herkes kanala gönderi attırabilirdi.
        settings = Settings(target_chat_id="-100123")
        self.assertFalse(settings.can_broadcast(42))
        self.assertIn("yetkili kullanıcı listesi", settings.broadcast_hint())

    def test_allows_whitelisted_user(self):
        settings = Settings(target_chat_id="-100123", allowed_chat_ids=frozenset({42}))
        self.assertTrue(settings.can_broadcast(42))
        self.assertFalse(settings.can_broadcast(43))

    def test_hint_mentions_missing_target(self):
        self.assertIn("TELEGRAM_TARGET_CHAT_ID", Settings().broadcast_hint())


if __name__ == "__main__":
    unittest.main()
