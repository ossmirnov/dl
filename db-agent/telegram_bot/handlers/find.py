import html

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from ..config import ADMIN_ID
from ..db import is_approved, save_message
from ..patterns import parse_address, parse_email, parse_name, parse_phone
from ..search import search_address, search_email, search_name, search_phone, to_yaml

_NOTHING_FOUND = 'Nothing found 👀'


async def handle_find(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    msg = update.message
    assert msg.from_user
    user = msg.from_user
    if user.id != ADMIN_ID and not await is_approved(user.id, user.username):
        return

    query = ' '.join(context.args or [])
    if not query:
        sent = await msg.reply_text('Usage: /find <phone|email|name|address>')
        await save_message(sent)
        return

    result = await _try_pattern_match(query)
    if result is None:
        sent = await msg.reply_text('Unrecognized format 🤷‍♂️')
        await save_message(sent)
        return

    reply = f'<pre>{html.escape(to_yaml(result))}</pre>' if result else _NOTHING_FOUND
    sent = await msg.reply_text(reply, parse_mode=ParseMode.HTML)
    await save_message(sent)


async def _try_pattern_match(text: str) -> dict | list | None:
    if phone := parse_phone(text):
        return await search_phone(phone)

    if email := parse_email(text):
        return await search_email(email)

    if name := parse_name(text):
        return await search_name(*name)

    if addr := parse_address(text):
        return await search_address(*addr)

    return None
