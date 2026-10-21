# Contributing

## Development principles

- Keep business logic out of the UI.
- Use type hints for public interfaces.
- Add tests for new behavior and edge cases.
- Validate uploaded content as untrusted input.
- Never introduce secrets or private data into Git.
- Document architectural decisions when they materially change.

## Before submitting a change

Run:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest