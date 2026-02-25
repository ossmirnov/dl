# Project Preferences

## Code Style Rules
- **No comments** - code should be self-explanatory
- **No docstrings** - see above
- **Single quotes only** - use `'like this'` not `"like this"`

## Python
- **Keyword arguments** when multiple arguments of the same type or at least 3 arguments
- Use * to force optional arguments to be keyword-only: `f(obvious_argument: ObviousType, *, optional_argument: str | None = None)`.
- **Modern typing annotations** - use `list[int] | None` not `Optional[List[int]]`.
- Check typing with `pyright`.
- Add packages to `requirements.txt` with their newest version. Run `pip install -r requirements.txt`.

## Unit tests
- For isolated functions with complex logic, write `pytest` comprehensive unit tests in a test/ subfolder.

## SQL Best Practices
- Write performant, production-grade PostgreSQL queries.
- Leverage **PostgreSQL-specific features** - window functions, LATERAL joins, FILTER clauses, functions, etc.
- Use best practices for performance. When updating entire column, drop the index first and create a new one afterwards.
- Always interact with database via MCP instead of bash `psql` and other CLI commands.
- In Python, always use ORM as much as possible instead of building commands with strings, never use text('SELECT ...'), etc.
