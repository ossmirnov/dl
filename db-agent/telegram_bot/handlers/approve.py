import re

from telegram import Update
from telegram.ext import ContextTypes

from ..config import ADMIN_ID
from ..db import approve_by_id, approve_by_username, is_approved, save_message

_ID_RE = re.compile(r'^\d+$')
_USERNAME_RE = re.compile(r'^@?(\w+)$')


async def handle_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    msg = update.message
    assert msg.from_user
    user = msg.from_user

    if user.id != ADMIN_ID:
        if await is_approved(user.id, user.username):
            sent = await msg.reply_text('Unknown command 🤷‍♂️')
            await save_message(sent)
        return

    args = context.args or []
    if not args:
        sent = await msg.reply_text('Usage: /approve @username or /approve user_id')
        await save_message(sent)
        return

    target = args[0]
    if _ID_RE.match(target):
        await approve_by_id(int(target))
        sent = await msg.reply_text(f'Approved user {target} ✅')
        await save_message(sent)
    elif m := _USERNAME_RE.match(target):
        await approve_by_username(m.group(1))
        sent = await msg.reply_text(f'Approved @{m.group(1)} ✅')
        await save_message(sent)
    else:
        sent = await msg.reply_text('Invalid format. Use /approve @username or /approve user_id')
        await save_message(sent)
