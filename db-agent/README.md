# OSINT Agent

- I implemented an investigator agent that searches for information in an attached database, identifying patterns and connections.
- Uses pre-implemented search tools, plus an MCP server for **arbitrary PostgreSQL queries**.
- Wrapped an agent in a **telegram bot**.

# Multi-Agent System

- I created a [calendar agent](./calendar-warm-up.ipynb) using [OpenAI Agent SDK](https://openai.github.io/openai-agents-python/agents/) and an open-source [MCP Server](https://github.com/nspady/google-calendar-mcp).
- I tried [`arcee-ai/trinity-large-preview:free`](https://openrouter.ai/arcee-ai/trinity-large-preview:free) model, but it was too dumb with tools. So I upgraded to [`google/gemini-3-flash-preview`](https://openrouter.ai/google/gemini-3-flash-preview).
- I created a subagent, that is used [as a tool](https://openai.github.io/openai-agents-python/tools/#agents-as-tools).
- I added [guardrail](https://openai.github.io/openai-agents-python/guardrails/) to filter out unrelated queries with a lightweight model. It runs concurrently with the main agent and terminates it once unrelated query is detected.

### Resources

- Alternative way to create multi-agent systems is using [handoffs](https://openai.github.io/openai-agents-python/handoffs/), that allow a router to forward queries to specialized agents.
- To control arguments passed to an MCP server tool, one can create a middle-layer MCP server using [FastMCP](https://github.com/jlowin/fastmcp) ([tutorial](https://share.google/aimode/90BVtalLU5YHFg5op)).
- To create multi-turn chat agents, one should use [sessions](https://openai.github.io/openai-agents-python/sessions/) for context memory management.
