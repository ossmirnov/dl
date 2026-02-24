import os
from pathlib import Path
from string import Template

from agents import (
    Agent,
    GuardrailFunctionOutput,
    ModelSettings,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
)
from agents.extensions.models.litellm_model import LitellmModel
from agents.mcp import MCPServerStdio
from pydantic import BaseModel, Field

from session import PostgresSession

PROJECT_ROOT = Path(__file__).parent.parent
RETRIEVAL_DIR = PROJECT_ROOT / 'retrieval'

litellm_model = LitellmModel(
    model='openrouter/google/gemini-3-flash-preview',
    base_url='https://openrouter.ai/api/v1/',
    api_key=os.environ['OPENROUTER_KEY'],
)

light_model = LitellmModel(
    model='openrouter/google/gemini-2.5-flash-lite',
    base_url='https://openrouter.ai/api/v1/',
    api_key=os.environ['OPENROUTER_KEY'],
)

reasoning_low = ModelSettings(extra_body={'reasoning': {'enabled': True, 'effort': 'medium'}})

with open(Path(__file__).parent / 'system.md') as f:
    _template = Template(f.read())
with open(PROJECT_ROOT / 'data' / 'db_description.md') as f:
    INSTRUCTIONS = _template.substitute(DATABASE_DESCRIPTION=f.read())


class GuardrailOutput(BaseModel):
    is_allowed: bool = Field(description='Whether the query is allowed.')
    rejection_reason: str | None = Field(default=None)


with open(Path(__file__).parent / 'guardrail.md') as f:
    _guardrail_instructions = f.read()

_guardrail_agent = Agent(
    name='guardrail-agent',
    instructions=_guardrail_instructions,
    model=light_model,
    output_type=GuardrailOutput,
)


@input_guardrail
async def osint_guardrail(
    ctx: RunContextWrapper[None], _agent: Agent, input: str | list[TResponseInputItem]
) -> GuardrailFunctionOutput:
    result = await Runner.run(_guardrail_agent, input, context=ctx.context)
    assert isinstance(result.final_output, GuardrailOutput)
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=not result.final_output.is_allowed,
    )


def get_retrieval_server():
    return MCPServerStdio(
        name='retrieval',
        params={
            'command': str(RETRIEVAL_DIR / 'mcp_server.py'),
        },
        client_session_timeout_seconds=120,
    )


def get_dbhub_server():
    return MCPServerStdio(
        name='dbhub',
        params={
            'command': 'npx',
            'args': ['-y', '@bytebase/dbhub@latest', '--config', str(PROJECT_ROOT / 'dbhub.toml')],
        },
        client_session_timeout_seconds=60,
    )


async def run_osint(
    query: str, session_id: str | None = None, enable_guardrail: bool = False
) -> str:
    session = PostgresSession(session_id) if session_id else None
    async with get_retrieval_server() as retrieval, get_dbhub_server() as dbhub:
        agent = Agent(
            name='osint-agent',
            instructions=INSTRUCTIONS,
            model=litellm_model,
            model_settings=reasoning_low,
            mcp_servers=[retrieval, dbhub],
            input_guardrails=[osint_guardrail] if enable_guardrail else [],
        )
        result = await Runner.run(agent, query, session=session, max_turns=30)
    return result.final_output
