from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / '.env')

import logging
import os
from datetime import datetime

import litellm
from agents import set_trace_processors
from opik.integrations.openai.agents import OpikTracingProcessor
from osint_agent.session import ensure_db as _ensure_osint_db
from telegram.ext import Application

from .config import TOKEN
from .db import ensure_db
from .handlers import register_handlers
from .notify import TelegramErrorHandler
from .search import init_retrieval

_log_dir = Path(__file__).parent / 'log'
_log_dir.mkdir(exist_ok=True)
_log_file = _log_dir / f'{datetime.now().strftime("%Y-%m-%dT%H.%M.%S.%f")}.log'
_log_latest = _log_dir / 'latest'
_log_latest.unlink(missing_ok=True)
_log_latest.symlink_to(_log_file.name)

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(_log_file),
    ],
)
logging.getLogger('mcp.os.posix.utilities').setLevel(logging.ERROR)
logging.getLogger('opik').propagate = True
litellm.suppress_debug_info = True

os.environ['OPIK_PROJECT_NAME'] = 'db-agent-bot'
set_trace_processors(processors=[OpikTracingProcessor()])


async def _post_init(_app: Application) -> None:
    await _ensure_osint_db()
    await ensure_db()
    await init_retrieval()


def main() -> None:
    app = Application.builder().token(TOKEN).post_init(_post_init).build()
    logging.getLogger().addHandler(TelegramErrorHandler(app.bot))
    register_handlers(app)
    app.run_polling()


if __name__ == '__main__':
    main()
