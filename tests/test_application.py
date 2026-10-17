"""Unit tests for the vacancy application form without Telegram network access."""

import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

# Configuration is validated at import time.
os.environ.setdefault("BOT_TOKEN", "123456:TEST_TOKEN")
os.environ.setdefault("ADMIN_ID", "123456789")

from main import (  # noqa: E402
    ApplicationForm,
    build_summary,
    confirm_yes,
    process_age,
    process_city,
    process_full_name,
)


def fake_message(text):
    return SimpleNamespace(text=text, answer=AsyncMock())


class FormTests(unittest.IsolatedAsyncioTestCase):
    async def test_non_text_name_is_rejected(self):
        message = fake_message(None)
        state = SimpleNamespace(update_data=AsyncMock(), set_state=AsyncMock())
        await process_full_name(message, state)
        state.update_data.assert_not_awaited()
        message.answer.assert_awaited_once()

    async def test_non_text_age_is_rejected(self):
        message = fake_message(None)
        state = SimpleNamespace(update_data=AsyncMock(), set_state=AsyncMock())
        await process_age(message, state)
        state.set_state.assert_not_awaited()

    async def test_invalid_age_is_rejected(self):
        for age in ("13", "81", "abc", "٢٥"):
            with self.subTest(age=age):
                message = fake_message(age)
                state = SimpleNamespace(update_data=AsyncMock(), set_state=AsyncMock())
                await process_age(message, state)
                state.update_data.assert_not_awaited()

    async def test_valid_age_advances_state(self):
        message = fake_message("25")
        state = SimpleNamespace(update_data=AsyncMock(), set_state=AsyncMock())
        await process_age(message, state)
        state.update_data.assert_awaited_once_with(age="25")
        state.set_state.assert_awaited_once_with(ApplicationForm.city)

    async def test_long_city_is_rejected(self):
        message = fake_message("X" * 101)
        state = SimpleNamespace(update_data=AsyncMock(), set_state=AsyncMock())
        await process_city(message, state)
        state.update_data.assert_not_awaited()

    def test_summary_escapes_user_html(self):
        summary = build_summary({"full_name": "<b>Test & Co</b>", "about": "<script>alert(1)</script>"})
        self.assertIn("&lt;b&gt;Test &amp; Co&lt;/b&gt;", summary)
        self.assertIn("&lt;script&gt;", summary)
        self.assertNotIn("<script>", summary)


class DeliveryTests(unittest.IsolatedAsyncioTestCase):
    def make_objects(self):
        message = SimpleNamespace(answer=AsyncMock(), delete=AsyncMock())
        callback = SimpleNamespace(
            from_user=SimpleNamespace(id=123, full_name="Candidate <Test>", username="candidate"),
            message=message,
            answer=AsyncMock(),
        )
        state = SimpleNamespace(
            get_data=AsyncMock(return_value={"photo_file_id": "photo_123", "full_name": "Candidate"}),
            clear=AsyncMock(),
        )
        bot = SimpleNamespace(send_photo=AsyncMock(), send_message=AsyncMock())
        return callback, state, bot

    async def test_failed_delivery_preserves_form(self):
        callback, state, bot = self.make_objects()
        bot.send_photo.side_effect = RuntimeError("network unavailable")
        await confirm_yes(callback, state, bot)
        state.clear.assert_not_awaited()
        callback.answer.assert_awaited_once()
        self.assertTrue(callback.answer.await_args.kwargs["show_alert"])

    async def test_successful_delivery_clears_form(self):
        callback, state, bot = self.make_objects()
        await confirm_yes(callback, state, bot)
        bot.send_photo.assert_awaited_once()
        bot.send_message.assert_awaited_once()
        state.clear.assert_awaited_once()
        callback.message.answer.assert_awaited_once()

    async def test_missing_photo_preserves_form(self):
        callback, state, bot = self.make_objects()
        state.get_data.return_value = {}
        await confirm_yes(callback, state, bot)
        bot.send_photo.assert_not_awaited()
        state.clear.assert_not_awaited()


if __name__ == "__main__":
    unittest.main()
