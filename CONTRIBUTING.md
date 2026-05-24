# Contributing

## Commit convention
Conventional Commits (NFR-MAINT-004):
`feat|fix|docs|test|chore|refactor|perf(scope): message`

Example: `feat(fitness): add Hevy webhook handler`

## Branching
- `main` is protected; CI must pass before merge.
- Feature branches: `feat/<short-name>`.

## Before committing
`pre-commit install` runs ruff + mypy automatically.
