from pathlib import Path

import yaml
from pydantic import BaseModel


class StartStrings(BaseModel):
    greeting: str


class MessageStrings(BaseModel):
    working_hard: str
    error: str
    admin_error_report: str


class FindStrings(BaseModel):
    usage: str
    unrecognized_format: str
    nothing_found: str


class ApproveStrings(BaseModel):
    usage: str
    approved_by_id: str
    approved_by_username: str
    invalid_format: str


class Strings(BaseModel):
    unknown_command: str
    start: StartStrings
    message: MessageStrings
    find: FindStrings
    approve: ApproveStrings


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _load_strings() -> Strings:
    base_path = Path(__file__).parent
    data = yaml.safe_load((base_path / 'interface.yaml').read_text())
    local_path = base_path / 'interface.local.yaml'
    if local_path.exists():
        local_data = yaml.safe_load(local_path.read_text())
        if local_data:
            data = _deep_merge(data, local_data)
    return Strings.model_validate(data)


STRINGS: Strings = _load_strings()
