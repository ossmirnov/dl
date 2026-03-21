from .db import get_session_start_message_id


async def get_session_id(chat_id: int) -> str:
    start_id = await get_session_start_message_id(chat_id)
    return f'{chat_id}_{start_id or 0}'
