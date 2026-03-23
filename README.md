# MusicBrainzPy

Modern Python bindings for the [MusicBrainz](https://musicbrainz.org/) JSON API.

Thin wrapper around the [MusicBrainz Web Service v2](https://musicbrainz.org/doc/MusicBrainz_API) — handles rate limiting, authentication, and (de)serialization via Pydantic models. All responses use the JSON API (`fmt=json`).

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone https://github.com/zas/musicbrainzpy.git
cd musicbrainzpy
uv sync
```

## Development

```bash
uv sync
uv run pytest tests/ -v
uv run ruff check .
uv run ruff format .
uv run ty check
```

## License

[GPL-3.0-or-later](LICENSE)
