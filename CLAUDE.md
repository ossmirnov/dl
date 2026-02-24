# Project Preferences

## Code Style Rules
- **No comments** - code should be self-explanatory
- **No docstrings** - see above
- **Single quotes only** - use `'like this'` not `"like this"`

## SQL Best Practices
- Write performant, production-grade PostgreSQL queries.
- Leverage **PostgreSQL-specific features** - window functions, LATERAL joins, FILTER clauses, functions, etc.
- Use best practices for performance. When updating entire column, drop the index first and create a new one afterwards.
- Always interact with database via MCP instead of bash `psql` and other CLI commands.
