from sqlalchemy import BigInteger, Boolean, Column, Index, MetaData, String, Table, func, select, update
from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from telegram import Message, User

_HISTORY_DSN = 'postgresql+asyncpg://localhost/db_agent_history'

_metadata = MetaData()

_telegram_users = Table(
    'telegram_users',
    _metadata,
    Column('user_id', BigInteger, primary_key=True),
    Column('username', String, nullable=True),
    Column('full_name', String, nullable=False),
    Column('data', JSONB, nullable=False),
)

_telegram_messages = Table(
    'telegram_messages',
    _metadata,
    Column('id', BigInteger, autoincrement=True, primary_key=True),
    Column('chat_id', BigInteger, nullable=False),
    Column('message_id', BigInteger, nullable=False),
    Column('user_id', BigInteger, nullable=False),
    Column('text', String, nullable=True),
    Column('is_command', Boolean, nullable=False),
    Column('data', JSONB, nullable=False),
    Column('sent_at', TIMESTAMP(timezone=True), nullable=True),
    Column('is_new_session', Boolean, nullable=False, server_default='false'),
    Column('is_from_bot', Boolean, nullable=False, server_default='false'),
    Column('is_deleted', Boolean, nullable=False, server_default='false'),
)

Index('ix_telegram_messages_chat_new_session', _telegram_messages.c.chat_id, _telegram_messages.c.is_new_session)

_approved_user_ids = Table(
    'approved_user_ids',
    _metadata,
    Column('user_id', BigInteger, primary_key=True),
)

_approved_usernames = Table(
    'approved_usernames',
    _metadata,
    Column('username', String, primary_key=True),
)

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(_HISTORY_DSN, pool_size=5, max_overflow=0)
    return _engine


async def ensure_db() -> None:
    async with get_engine().begin() as conn:
        await conn.run_sync(_metadata.create_all)


async def upsert_user(user: User) -> None:
    data = user.to_dict()
    stmt = (
        insert(_telegram_users)
        .values(user_id=user.id, username=user.username, full_name=user.full_name, data=data)
        .on_conflict_do_update(
            index_elements=['user_id'],
            set_={'username': user.username, 'full_name': user.full_name, 'data': data},
        )
    )
    async with get_engine().begin() as conn:
        await conn.execute(stmt)


async def save_message(message: Message) -> None:
    assert message.from_user
    from telegram.constants import MessageEntityType

    is_cmd = bool(
        message.text
        and message.entities
        and any(e.type == MessageEntityType.BOT_COMMAND and e.offset == 0 for e in message.entities)
    )
    async with get_engine().begin() as conn:
        prev_sent_at = await conn.scalar(
            select(_telegram_messages.c.sent_at)
            .where(_telegram_messages.c.chat_id == message.chat_id)
            .order_by(_telegram_messages.c.message_id.desc())
            .limit(1)
        )
        is_new_session = (
            message.text == '/start'
            or prev_sent_at is None
            or (message.date - prev_sent_at).total_seconds() >= 300
        )
        await conn.execute(
            insert(_telegram_messages).values(
                chat_id=message.chat_id,
                message_id=message.message_id,
                user_id=message.from_user.id,
                text=message.text,
                is_command=is_cmd,
                is_new_session=is_new_session,
                is_from_bot=message.from_user.is_bot,
                sent_at=message.date,
                data=message.to_dict(),
            )
        )


async def is_approved(user_id: int, username: str | None) -> bool:
    async with get_engine().connect() as conn:
        if await conn.scalar(
            select(_approved_user_ids.c.user_id).where(_approved_user_ids.c.user_id == user_id)
        ):
            return True
        if username and await conn.scalar(
            select(_approved_usernames.c.username).where(
                _approved_usernames.c.username == username.lower()
            )
        ):
            return True
    return False


async def approve_by_id(user_id: int) -> None:
    async with get_engine().begin() as conn:
        await conn.execute(
            insert(_approved_user_ids).values(user_id=user_id).on_conflict_do_nothing()
        )


async def approve_by_username(username: str) -> None:
    async with get_engine().begin() as conn:
        await conn.execute(
            insert(_approved_usernames).values(username=username.lower()).on_conflict_do_nothing()
        )


async def get_session_start_message_id(chat_id: int) -> int | None:
    async with get_engine().connect() as conn:
        return await conn.scalar(
            select(func.max(_telegram_messages.c.message_id))
            .where(_telegram_messages.c.chat_id == chat_id)
            .where(_telegram_messages.c.is_new_session.is_(True))
        )


async def mark_message_deleted(chat_id: int, message_id: int) -> None:
    async with get_engine().begin() as conn:
        await conn.execute(
            update(_telegram_messages)
            .where(_telegram_messages.c.chat_id == chat_id)
            .where(_telegram_messages.c.message_id == message_id)
            .values(is_deleted=True)
        )
