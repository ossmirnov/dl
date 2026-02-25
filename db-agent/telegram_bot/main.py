from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

import logging
import os

import litellm
from agents import set_trace_processors
from opik.integrations.openai.agents import OpikTracingProcessor
from osint_agent.session import ensure_db as _ensure_osint_db
from telegram.ext import Application

from .config import TOKEN
from .db import ensure_db
from .handlers import register_handlers
from .search import init_retrieval

logging.basicConfig(level=logging.INFO)
logging.getLogger('mcp.os.posix.utilities').setLevel(logging.ERROR)
litellm.suppress_debug_info = True

os.environ['OPIK_PROJECT_NAME'] = 'db-agent-bot'
set_trace_processors(processors=[OpikTracingProcessor()])


async def _post_init(app: Application) -> None:
    await _ensure_osint_db()
    await ensure_db()
    await init_retrieval()


def main() -> None:
    app = Application.builder().token(TOKEN).post_init(_post_init).build()
    register_handlers(app)
    app.run_polling()


if __name__ == '__main__':
    main()
