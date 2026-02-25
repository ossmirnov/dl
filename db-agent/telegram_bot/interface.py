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


class Strings(BaseModel):
    unknown_command: str
    start: StartStrings
    message: MessageStrings
    find: FindStrings
    approve: ApproveStrings


STRINGS: Strings = Strings.model_validate(
    yaml.safe_load((Path(__file__).parent / 'interface.yaml').read_text())
)
