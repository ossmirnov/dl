from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, TypeHandler, filters

from .approve import handle_approve
from .find import handle_find
from .logging import log_update
from .message import handle_message, handle_unknown_command
from .start import handle_start


def register_handlers(app: Application) -> None:
    app.add_handler(TypeHandler(Update, log_update), group=-1)
    app.add_handler(CommandHandler('start', handle_start))
    app.add_handler(CommandHandler('approve', handle_approve))
    app.add_handler(CommandHandler('find', handle_find))
    app.add_handler(MessageHandler(filters.COMMAND, handle_unknown_command))
    app.add_handler(MessageHandler(~filters.COMMAND, handle_message))
