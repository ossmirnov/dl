import logging
import secrets
import string
from dataclasses import dataclass, field

from fastapi import WebSocket

from game.engine import GameState, new_game
from game.types import Color


log = logging.getLogger(__name__)

ROOM_ID_ALPHABET = string.ascii_uppercase + string.digits
ROOM_ID_LENGTH = 8


def _new_room_id() -> str:
    return ''.join(secrets.choice(ROOM_ID_ALPHABET) for _ in range(ROOM_ID_LENGTH))


@dataclass
class Room:
    room_id: str
    state: GameState
    sockets: list[WebSocket] = field(default_factory=list)
    sessions: dict[str, Color | None] = field(default_factory=dict)
    socket_session: dict[int, str] = field(default_factory=dict)


class RoomRegistry:
    def __init__(self) -> None:
        self._rooms: dict[str, Room] = {}

    def create(self, *, seed: int | None = None) -> Room:
        while True:
            room_id = _new_room_id()
            if room_id not in self._rooms:
                break
        room = Room(room_id=room_id, state=new_game(seed=seed))
        self._rooms[room_id] = room
        log.info('room created room_id=%s seed=%s', room_id, seed)
        return room

    def get(self, room_id: str) -> Room | None:
        return self._rooms.get(room_id.upper())

    def assign_color(self, room: Room, *, ws: WebSocket, session_id: str) -> Color | None:
        if session_id in room.sessions:
            color = room.sessions[session_id]
        else:
            taken = {c for c in room.sessions.values() if c is not None}
            color = None
            for cand in (Color.RED, Color.BLUE):
                if cand not in taken:
                    color = cand
                    break
            room.sessions[session_id] = color
        room.socket_session[id(ws)] = session_id
        return color

    def find_old_socket(
        self, room: Room, *, session_id: str, exclude: WebSocket
    ) -> WebSocket | None:
        for s in room.sockets:
            if s is exclude:
                continue
            if room.socket_session.get(id(s)) == session_id:
                return s
        return None

    def release(self, room: Room, ws: WebSocket) -> None:
        room.socket_session.pop(id(ws), None)
        if ws in room.sockets:
            room.sockets.remove(ws)

    def rematch(self, room: Room) -> None:
        room.state = new_game(seed=None)
        log.info('room rematch room_id=%s', room.room_id)


registry = RoomRegistry()
