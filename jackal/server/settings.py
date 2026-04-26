import os
from pathlib import Path


PORT = int(os.environ.get('JACKAL_PORT', '8080'))
HOST = os.environ.get('JACKAL_HOST', '0.0.0.0')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WEB_DIR = PROJECT_ROOT / 'web' / 'static'
MEDIA_DIR = PROJECT_ROOT / 'web' / 'media'
LOG_DIR = PROJECT_ROOT / 'log'
