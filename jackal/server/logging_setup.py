import logging
import sys
from datetime import datetime
from pathlib import Path


def configure_logging(*, log_dir: Path) -> Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime('%Y-%m-%d__%H-%M-%S')
    path = log_dir / f'{stamp}.log'

    fmt = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    file_handler = logging.FileHandler(path, encoding='utf-8')
    file_handler.setFormatter(fmt)
    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setFormatter(fmt)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()
    root.addHandler(file_handler)
    root.addHandler(stream_handler)

    for noisy in ('uvicorn', 'uvicorn.access', 'uvicorn.error'):
        lg = logging.getLogger(noisy)
        lg.handlers.clear()
        lg.propagate = True
        lg.setLevel(logging.INFO)

    logging.getLogger(__name__).info('logging initialized at %s', path)
    return path
