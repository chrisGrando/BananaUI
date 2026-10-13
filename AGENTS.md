# AGENTS.md

## Project Setup and Management
- Always use PyPy to run and build the project
- In case PyPy is completely unavailable, using regular Python is allowed
- NEVER use any `git` commands unless explicitly asked in the prompt
- If installing a new package with pip is required, always use `pip install --user [package-name]`
- NEVER install a new package with pip in Python's root

## Environment
- All secrets are in environment variables. NEVER hardcode credentials.
- Required env vars are listed in `.env.example` (committed, values are placeholders).
- Actual values are in `.env` (gitignored).
- If you can't find a specific value in `.env`, then create it in the `.env`, NEVER hardcode it in the project source code

## Security Guidelines
- All database queries use parameterized statements (no string interpolation in SQL)
- Input validation at route level using Zod schemas
- NEVER log request bodies in production (may contain PII)
- NEVER hardcode API keys of any sort
- Do NOT hardcode service URLs unless said URL is harmless both inside and outside the project scope or context
