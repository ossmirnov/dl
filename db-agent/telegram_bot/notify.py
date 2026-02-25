import logging

from telegram import Bot

from .config import ADMIN_ID

logger = logging.getLogger(__name__)


async def notify_admin(bot: Bot, text: str) -> None:
    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception:
        logger.exception('Failed to notify admin')
