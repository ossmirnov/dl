import asyncio
import logging

from telegram import Message, Update
from telegram.constants import ChatAction, ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from osint_agent.agent import run_osint
from ..config import ADMIN_ID
from ..db import is_approved, mark_message_deleted, save_message
from ..notify import notify_admin
from ..tg_session import get_session_id

logger = logging.getLogger(__name__)


async def handle_unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    msg = update.message
    assert msg.from_user
    user = msg.from_user
    if user.id != ADMIN_ID and not await is_approved(user.id, user.username):
        return
    reply = await msg.reply_text('Unknown command 🤷‍♂️')
    await save_message(reply)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    assert update.message
    msg = update.message
    assert msg.from_user
    user = msg.from_user
    if user.id != ADMIN_ID and not await is_approved(user.id, user.username):
        return

    text = msg.text or msg.caption or ''
    if not text:
        return

    await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
    session_id = await get_session_id(msg.chat_id)
    try:
        response = await _invoke_agent(msg, text, session_id)
        sent = await _reply_html_or_plain(msg, response)
        await save_message(sent)
    except Exception:
        logger.exception('Agent error for user %d', user.id)
        await notify_admin(
            context.bot,
            f'❌ Agent error\n👤 {user.full_name} ({user.id})\n💬 {text}',
        )
        sent = await msg.reply_text('Something is broken! 🔧')
        await save_message(sent)


async def _invoke_agent(msg: Message, text: str, session_id: str) -> str:
    task = asyncio.create_task(run_osint(text, session_id=session_id))
    try:
        return await asyncio.wait_for(asyncio.shield(task), timeout=10)
    except asyncio.TimeoutError:
        pass
    wait_msg = await msg.reply_text('Working hard, please wait... 🔍')
    await save_message(wait_msg)
    try:
        return await task
    finally:
        await wait_msg.delete()
        await mark_message_deleted(wait_msg.chat_id, wait_msg.message_id)


async def _reply_html_or_plain(msg: Message, text: str) -> Message:
    try:
        return await msg.reply_text(text, parse_mode=ParseMode.HTML)
    except BadRequest:
        logger.warning('HTML reply failed, falling back to plain text (chat_id=%d): %r', msg.chat_id, text)
        return await msg.reply_text(text)
