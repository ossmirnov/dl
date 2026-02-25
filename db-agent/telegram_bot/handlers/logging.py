from telegram import Update
from telegram.ext import ContextTypes

from ..db import save_message, upsert_user
from ..notify import notify_admin


async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.from_user:
        return
    user = msg.from_user
    await upsert_user(user)
    await save_message(msg)
    await notify_admin(
        context.bot,
        f'👤 {user.full_name} (@{user.username} | {user.id})\n💬 {msg.text or "[no text]"}',
    )
