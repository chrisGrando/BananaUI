# AGENTS.md

## Project Setup and Management
- Prefer using PyPy to run and build the project
- In case PyPy is completely unavailable, using regular Python is allowed
- NEVER use any `git` commands unless explicitly asked in the prompt

### On Windows systems
- ALWAYS check if PyPy is located at `<Project Root>/bin/pypy`
  - If it isn't, then run `SETUP_PROJECT_WINDOWS.bat` before doing anything else
    - Watch out for any error or warning messages when running `SETUP_PROJECT_WINDOWS.bat`
  - If it is, then prefer using the locally installed PyPy over any global installations
- Prefer using resources bundled within the project repository (such as the files in the `assets` folder)
- ALWAYS install a new package with pip in PyPy's root
- Run the project by using the `RUN_PROJECT_WINDOWS.bat` script

### On UNIX systems
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
