# Jackal

Browser-based Jackal-style treasure game. Two players, 10x10 closed map, FastAPI + WebSockets, Python game logic.

## Run with Docker

```
docker compose up -d --build
```

Then open `http://<server-ip>:8080/` in two browsers, create a room in one, paste the room link into the other.

Override port: `JACKAL_PORT=9000 docker compose up -d`.

## Run locally

```
pip install -r requirements.txt
uvicorn server.app:app --host 0.0.0.0 --port 8080 --reload
```

## Tests

```
pytest test/ -v
pyright .
```

## Media

Drop PNGs into `web/media/`. The frontend loads `/media/tile_<type>.png` for each cell type and `/media/player_<color>.png` for each player. Missing files render as colored squares with a label, so the game is fully playable before any art is provided.

Filenames: `tile_closed.png`, `tile_empty.png`, `tile_money.png`, `tile_swap.png`, `tile_tunnel.png`, `tile_double.png`, `tile_fly.png`, `tile_swamp.png`, `tile_teleport.png`, `tile_stone.png`, `tile_thief.png`, `tile_wizard.png`, `tile_normalize.png`, `tile_home_red.png`, `tile_home_blue.png`, `player_red.png`, `player_blue.png`. 96×96 transparent PNG recommended for tiles, 64×64 for players.

## Logs

Each server start opens a fresh log at `log/<YYYY-MM-DD__HH-MM-SS>.log` capturing every move, reveal, and effect.

## Public URL

Game is reachable on `http://<server-public-ip>:8080/`. To put it behind a domain or HTTPS, terminate TLS in a reverse proxy (nginx, Caddy, traefik) and forward to the container's port 8080.
