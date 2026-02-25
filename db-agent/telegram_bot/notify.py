import asyncio
import logging

from telegram import Bot
from telegram.constants import MessageLimit

from .config import ADMIN_ID

logger = logging.getLogger(__name__)

_TRUNCATION_MARKER = '\n...[truncated]...\n'


def _truncate(text: str) -> str:
    limit = MessageLimit.MAX_TEXT_LENGTH
    if len(text) <= limit:
        return text
    keep = (limit - len(_TRUNCATION_MARKER)) // 2
    return text[:keep] + _TRUNCATION_MARKER + text[-keep:]


def split_by_newlines(text: str) -> list[str]:
    limit = MessageLimit.MAX_TEXT_LENGTH
    parts: list[str] = []
    current: list[str] = []
    current_len = 0
    for line in text.split('\n'):
        line_len = len(line) + 1
        if current and current_len + line_len > limit:
            parts.append('\n'.join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len
    if current:
        parts.append('\n'.join(current))
    return parts


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
            loop.create_task(self._bot.send_message(chat_id=ADMIN_ID, text=_truncate(self.format(record))))
        except RuntimeError:
            pass
        except Exception:
            self.handleError(record)
