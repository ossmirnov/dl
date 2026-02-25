import asyncio
import logging

from telegram import Bot

from .config import ADMIN_ID

logger = logging.getLogger(__name__)


async def notify_admin(bot: Bot, text: str) -> None:
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception:
        logger.exception('Failed to notify admin')


class TelegramErrorHandler(logging.Handler):
    def __init__(self, bot: Bot) -> None:
        super().__init__(level=logging.ERROR)
        self._bot = bot

    def emit(self, record: logging.LogRecord) -> None:
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._bot.send_message(chat_id=ADMIN_ID, text=self.format(record)))
        except RuntimeError:
            pass
        except Exception:
            self.handleError(record)
