# Copilot instructions for ARYSTOS Core

## Build, test, and lint

Run these commands from the `arystos-core` project root:

```bash
python -m pip install -e ".[dev]"
ruff check server/
ruff format server/
mypy server/
pytest server/tests/ -x
```

Run one test by its pytest node ID, for example:

```bash
pytest server/tests/test_auth.py::test_tokens_equal_returns_true_for_equal -q
```

The SQL interpolation checker can be run with `python tools/check_sql.py`. CI uses Python 3.12 and runs Ruff, strict mypy, and pytest; the package also declares Python 3.12 as its minimum. The pre-commit hooks run formatting, Ruff with autofixes, mypy, and the tests.

## Architecture

The repository is the Python `server` package. The implemented foundation currently includes:

- `server/auth/token.py` for token generation, SHA-256 hashing, constant-time comparison, and Bearer-header parsing.
- `server/config.py` for Pydantic Settings configuration, including `.env` loading.
- `server/database/connection.py` for SQLite connections and ordered, transactional SQL migrations from `server/database/migrations/`; applied filenames are tracked in `schema_migrations`.
- `server/tests/` for pytest coverage of the implemented behavior.

The intended broader server design is documented in `../../docs/arystos-core-lld-final.md`. It separates authentication, repositories, services, and routers; repositories handle persistence, services own business rules, and routers expose the HTTP contracts. Treat that as the design target, not as a description of modules that already exist. In particular, the current connection module uses synchronous `sqlite3`, even though the design document describes an async database layer.

## Project-specific conventions

- Use the design document as the source for planned API, schema, and business behavior. Keep it in sync when changing a locked design decision.
- Add database changes as new, sequentially named SQL migration files. The runner applies files in filename order, records each successful migration, and propagates failures after rolling back the migration transaction.
- Keep SQL values parameterized; do not interpolate values into SQL strings. Run `python tools/check_sql.py` when changing SQL construction.
- Token comparisons must use `secrets.compare_digest` via `tokens_equal`; do not compare raw tokens with `==`. Store token hashes rather than raw client tokens.
- Read configuration through `Settings` in `server/config.py`; `.env` is ignored by Git.
- Keep pytest tests under `server/tests/`, named `test_*.py` with test functions named `test_*`. Pytest asyncio mode is configured as `auto`.
- Ruff is configured for a 100-character line length and Python 3.12, with the `E`, `F`, `W`, `I`, `N`, `UP`, `B`, and `SIM` rule families enabled. Mypy runs in strict mode.


# Copilot instructions for ARYSTOS Core

## Build, test, and lint
[existing content — keep]

## Architecture
[existing content — keep]

## Project-specific conventions
[existing content — keep]

---

# ARYSTOS — Quality Rules

Apply these rules to every file you generate or edit.

## Code is written for humans
The computer runs the code. People maintain it.

## Naming and structure
- Descriptive names. No abbreviations. No single-letter variables except loop indices.
- Functions do one thing. Ideal length 5–20 lines.
- Minimal parameters. If a function takes more than three, consider a dataclass.
- No cleverness. KISS. DRY.

## Comments and docstrings
- Docstrings on every public function: what it does, what it takes, what it returns, what it raises.
- Comments explain WHY, not WHAT.
- No commented-out code.

## Errors and validation
- Fail loud and early. Raise specific exceptions with descriptive messages. Never `except: pass`.
- Validate input at the boundary (routers, CLI). Never trust user input.
- No stack traces to clients. Full traceback to the log.

## Security
- Parameterized SQL only. No f-strings inside SQL. No `.format()`. No `%`.
- Secrets in environment variables. Never in code, never in git.
- Constant-time comparison for tokens. `secrets.compare_digest`, never `==`.

## Testing
- Tests written before or alongside code.
- Cover the happy path, the edge cases, and the failure modes.
- The test name says what it verifies.
- Every function in the LLD has a named test.

## Refactoring
- Boy Scout Rule. Leave the code cleaner than you found it.
- Surgical refactors as part of every task.
- Never refactor and add a feature in the same commit.

## User-facing behavior
- Error responses have a consistent shape: `{"error": "<code>", "detail": "<optional>"}`.
- Messages are clear and actionable.
- Never expose internal state, file paths, library versions, or stack traces to clients.

## What to avoid
- No premature optimization.
- No global mutable state.
- No hidden side effects. A function named `get_x` does not write to the database.
- No code that exists only because "we might need it later."
- No comments that repeat the code.

## Conflict rule
If the LLD and these rules conflict, the LLD wins. Report the conflict before proceeding.