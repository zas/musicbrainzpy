# Agent Guidelines

Rules for AI agents working on this project.

## Architecture

- Python package: `musicbrainzpy/`
- Async-first client built on `httpx`, with sync wrapper
- Pydantic v2 models for all MusicBrainz entities
- `DEFAULT_BASE_URL` in `client.py`, overridable via constructor
- Rate limiter in `_ratelimit.py` enforces 1 req/s

## Code Style

- `from __future__ import annotations` in every file
- Imports at the top, never inline
- Type hints on all function signatures
- Docstrings on all public classes and methods
- Line length limit: 120 characters
- Prefer helpers over repeated code — extract common patterns
- Keep functions short and focused
- Run `uv run ruff format .` and `uv run ruff check .` before every commit
- Run `uv run ty check` before every commit
- Use `uv run` for all commands — never invoke `python`, `pytest`, `ruff` directly

## Testing

- Tests in `tests/` using `pytest` and `pytest-asyncio`
- Mock HTTP with `respx` — never hit the network
- Sample JSON responses as constants in `tests/conftest.py`
- Test helpers and internals in `tests/test_client.py`
- Test model deserialization in `tests/test_models.py`
- Run tests: `uv run pytest tests/ -v`

## Conventions

- Entity type strings use kebab-case to match the API (`release-group`, not `release_group`)
- Pydantic models use `alias` for kebab-case JSON keys → snake_case attributes
- All models use `model_config = ConfigDict(extra="allow")` for forward compatibility
- Optional fields for data that depends on `inc=` parameters
- `SearchResult[T]` and `BrowseResult[T]` generic wrappers for list responses

## Common Pitfalls

- Release ID ≠ Release Group ID — never interchangeable
- The JSON API uses `fmt=json` query param or `Accept: application/json` header
- Submissions (POST) require XML bodies — the only XML in the project
- Rate limit is 1 request per second, not per endpoint
- `inc=` values are joined with `+` in the URL
