import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from game.engine import apply_move
from game.types import Color, Direction

from .rooms import Room, registry
from .serialize import events_to_list, state_to_dict


log = logging.getLogger(__name__)


async def _send_state(room: Room) -> None:
    payload = {'type': 'state', 'state': state_to_dict(room.state)}
    events = events_to_list(room.state.events)
    if events:
        room.state.events.clear()
    dead: list[WebSocket] = []
    for ws in list(room.sockets):
        try:
            await ws.send_json(payload)
            if events:
                await ws.send_json({'type': 'events', 'events': events})
        except Exception:
            dead.append(ws)
    for d in dead:
        registry.release(room, d)


async def _send_error(ws: WebSocket, message: str) -> None:
    try:
        await ws.send_json({'type': 'error', 'message': message})
    except Exception:
        pass


def _parse_direction(value: Any) -> Direction:
    return Direction(value)


def _parse_pos(payload: dict[str, Any]) -> tuple[int, int]:
    return (int(payload['r']), int(payload['c']))


async def handle_socket(ws: WebSocket, room_id: str) -> None:
    await ws.accept()
    room = registry.get(room_id)
    if room is None:
        await _send_error(ws, f'room not found: {room_id}')
        await ws.close()
        return

    color = registry.assign_color(room, ws)
    room.sockets.append(ws)
    log.info('ws joined room_id=%s color=%s', room_id, color.value if color else 'spectator')
    await ws.send_json({'type': 'assigned', 'color': color.value if color else 'spectator'})
    await _send_state(room)

    try:
        while True:
            msg = await ws.receive_json()
            kind = msg.get('type')
            if kind == 'move':
                if color is None:
                    await _send_error(ws, 'spectators cannot move')
                    continue
                try:
                    direction = _parse_direction(msg.get('dir'))
                    apply_move(room.state, color=color, direction=direction)
                except ValueError as e:
                    await _send_error(ws, str(e))
                    continue
                log.info('move room_id=%s color=%s dir=%s', room_id, color.value, direction.value)
                await _send_state(room)
            elif kind == 'fly':
                if color is None:
                    await _send_error(ws, 'spectators cannot move')
                    continue
                try:
                    target = _parse_pos(msg)
                    apply_move(room.state, color=color, fly_to=target)
                except (ValueError, KeyError) as e:
                    await _send_error(ws, str(e))
                    continue
                log.info('fly room_id=%s color=%s to=%s', room_id, color.value, target)
                await _send_state(room)
            elif kind == 'rematch':
                if room.state.winner is None:
                    await _send_error(ws, 'game still in progress')
                    continue
                registry.rematch(room)
                await _send_state(room)
            elif kind == 'state':
                await _send_state(room)
            else:
                await _send_error(ws, f'unknown message type: {kind}')
    except WebSocketDisconnect:
        log.info('ws disconnect room_id=%s color=%s', room_id, color.value if color else 'spectator')
    except Exception:
        log.exception('ws error room_id=%s', room_id)
    finally:
        registry.release(room, ws)
