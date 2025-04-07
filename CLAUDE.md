# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: S3 Navigator

### Build & Run Commands (using uv/uvx)
- Create venv: `uv venv`
- Install package: `uv pip install -e .`
- Install dev dependencies: `uv pip install -e ".[dev]"`
- Run application: `s3-navigator`
- Run with profile: `s3-navigator --profile <profile_name> --region <region_name>`
- Run tests: `uv run pytest`
- Run single test: `uv run pytest tests/test_file.py::test_function`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Typecheck: `uv run mypy s3_navigator`

### Code Style Guidelines
- **Python Version**: 3.9+
- **Formatting**: Ruff formatter with 88 character line length
- **Linting**: Ruff for comprehensive linting (includes isort, flake8, pydocstyle)
- **Imports**: Group standard library, third-party, and local imports with a blank line between
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Error Handling**: Use explicit exception types, handle AWS API errors gracefully
- **Documentation**: Google-style docstrings for all functions and classes
- **Type Hints**: Python type annotations for all function parameters and return values

### Dependencies
- Primary: boto3, click, textual, yaspin, termcolor
- Dev: pytest, ruff, mypy, types-boto3
- Default AWS region: eu-central-1