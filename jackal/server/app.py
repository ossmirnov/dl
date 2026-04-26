import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from urllib.parse import quote

from . import settings
from .logging_setup import configure_logging
from .rooms import registry
from .ws import handle_socket


log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    path = configure_logging(log_dir=settings.LOG_DIR)
    log.info('jackal server start log=%s host=%s port=%s', path, settings.HOST, settings.PORT)
    yield
    log.info('jackal server stop')


app = FastAPI(lifespan=lifespan, title='Jackal')


@app.middleware('http')
async def no_cache_assets(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    if path.startswith('/static/') or path == '/' or path.startswith('/room/'):
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


settings.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount('/media', StaticFiles(directory=str(settings.MEDIA_DIR)), name='media')
app.mount('/static', StaticFiles(directory=str(settings.WEB_DIR)), name='static')


@app.get('/')
async def index() -> FileResponse:
    return FileResponse(settings.WEB_DIR / 'index.html')


@app.get('/room/{room_id}')
async def room_page(room_id: str):
    if registry.get(room_id) is None:
        return RedirectResponse(
            url=f'/?error=room_not_found&id={quote(room_id)}',
            status_code=303,
        )
    return FileResponse(settings.WEB_DIR / 'room.html')


@app.post('/api/rooms')
async def create_room(req: Request) -> JSONResponse:
    body: dict[str, Any] = {}
    try:
        body = await req.json()
    except Exception:
        body = {}
    seed_raw = body.get('seed') if isinstance(body, dict) else None
    seed: int | None = None
    if seed_raw is not None:
        try:
            seed = int(seed_raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail='seed must be int')
    room = registry.create(seed=seed)
    return JSONResponse({'room_id': room.room_id, 'seed': seed})


@app.websocket('/ws/{room_id}')
async def ws_route(websocket: WebSocket, room_id: str) -> None:
    session_id = websocket.query_params.get('session', '').strip()
    if not session_id:
        await websocket.close(code=4001)
        return
    await handle_socket(websocket, room_id, session_id)
