import logging
import secrets
from dataclasses import dataclass, field

from fastapi import WebSocket

from game.engine import GameState, new_game
from game.types import Color


log = logging.getLogger(__name__)


@dataclass
class Room:
    room_id: str
    state: GameState
    sockets: list[WebSocket] = field(default_factory=list)
    color_for: dict[int, Color | None] = field(default_factory=dict)


class RoomRegistry:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}

    def create(self, *, seed: int | None = None) -> Room:
        room_id = secrets.token_urlsafe(6)
        room = Room(room_id=room_id, state=new_game(seed=seed))
        self._rooms[room_id] = room
        log.info('room created room_id=%s seed=%s', room_id, seed)
        return room

    def get(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id)

    def assign_color(self, room: Room, ws: WebSocket) -> Color | None:
        taken = {c for c in room.color_for.values() if c is not None}
        for color in (Color.RED, Color.BLUE):
            if color not in taken:
                room.color_for[id(ws)] = color
                return color
        room.color_for[id(ws)] = None
        return None

    def release(self, room: Room, ws: WebSocket) -> None:
        room.color_for.pop(id(ws), None)
        if ws in room.sockets:
            room.sockets.remove(ws)

    def rematch(self, room: Room) -> None:
        room.state = new_game(seed=None)
        log.info('room rematch room_id=%s', room.room_id)


registry = RoomRegistry()
