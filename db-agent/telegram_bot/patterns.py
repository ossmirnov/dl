import re

_PHONE = re.compile(r'^\+\d{9,}$')
_EMAIL = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
_RU_NAME_PART = r'[А-ЯЁ][а-яё]+(?:-[А-ЯЁ][а-яё]+)?'
_NAME = re.compile(rf'^({_RU_NAME_PART}) ({_RU_NAME_PART}) ({_RU_NAME_PART})$')
_RU_WORD = r'[А-ЯЁ][а-яё]+'
_ADDRESS = re.compile(rf'^({_RU_WORD}) ({_RU_WORD}(?:\s{_RU_WORD})?) (\d\S*)(?:\s(\d+))?$')


def parse_phone(text: str) -> int | None:
    if _PHONE.match(text):
        return int(text.lstrip('+'))
    return None


def parse_email(text: str) -> str | None:
    return text if _EMAIL.match(text) else None


def parse_name(text: str) -> tuple[str, str, str] | None:
    m = _NAME.match(text)
    return (m.group(1), m.group(2), m.group(3)) if m else None


def parse_address(text: str) -> tuple[str, str, str, str | None] | None:
    m = _ADDRESS.match(text)
    return (m.group(1), m.group(2), m.group(3), m.group(4)) if m else None
