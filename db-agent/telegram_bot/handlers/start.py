from telegram import Update
from telegram.ext import ContextTypes

from ..config import ADMIN_ID
from ..db import is_approved, save_message


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    msg = update.message
    assert msg.from_user
    user = msg.from_user
    if user.id != ADMIN_ID and not await is_approved(user.id, user.username):
        return
    reply = await msg.reply_text('Hey! 👋')
    await save_message(reply)
