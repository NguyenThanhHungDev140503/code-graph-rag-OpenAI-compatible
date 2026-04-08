# Code-Graph-RAG Agent Guidelines

## Build/Lint/Test Commands

```bash
# Install dependencies
uv sync --extra treesitter-full          # Full development with all grammars
uv sync --extra test                     # With test dependencies

# Lint & Format (Ruff)
make lint    # or: uv run ruff check .
make format  # or: uv run ruff format .

# Type checking (Ty)
make typecheck    # or: uv run ty check --exclude codebase_rag/tests/

# Run a single test
uv run pytest codebase_rag/tests/test_class_ingest.py::TestClassIngest::test_method

# Run tests (parallel, skip slow integration)
make test-parallel   # or: uv run pytest -n auto -m "not integration"

# Full pre-commit check (run before every commit)
make pre-commit

# All checks + tests
make check  # lint + typecheck + test
```

## Code Style

### Imports
- Always use `from __future__ import annotations` at the top
- Use relative imports within package: `from . import constants as cs`
- Sort: stdlib → third-party → local, with blank lines between groups
- No wildcard imports (`from x import *`)

### Formatting (Ruff)
- Line length: 88 characters
- Quote style: double quotes
- Run `ruff format .` before committing

### Type Annotations
- Use type hints on all function signatures
- Use `TypedDict` for dict types, `Unpack` for generic kwargs
- Use `# type:` annotation comments only when unavoidable (per ALLOWED_COMMENT_MARKERS)

### Naming Conventions
- Classes: `PascalCase` (e.g., `class GraphNode`)
- Functions/methods: `snake_case` (e.g., `def process_definition`)
- Constants: `SCREAMING_SNAKE_CASE` in `constants.py`
- Private: `_leading_underscore`
- Types: `PascalCase` (from `types_defs.py`)

### No Docstrings or Comments
- **CRITICAL**: No module docstrings, class docstrings, or inline `#` comments
- Allowed markers only (see `constants.py` → `ALLOWED_COMMENT_MARKERS`):
  - `(H)` - Header section markers
  - `type:`, `# type:` - Type annotations
  - `noqa` - Ruff disable comments
  - `pyright` - Pyright directives
  - `ty:` - Tytyping comments
  - `@@protoc` - Protocol buffer markers
  - `nosec` - Bandit security

### Error Handling
- Custom errors defined in `exceptions.py` as module-level constants
- Exception classes inherit from `Exception` (e.g., `class LLMGenerationError(Exception): pass`)
- Use `raise` with descriptive error messages from `exceptions.py`
- Validate inputs early; fail fast with clear messages

### Project Structure
```
codebase_rag/
├── cli.py              # Typer CLI entry point
├── config.py           # Pydantic Settings + ModelConfig
├── constants.py        # All constants (colors, errors, settings)
├── exceptions.py       # Error constants + exception classes
├── models.py           # Pydantic/dataclass models
├── types_defs.py       # TypedDict definitions, type aliases
├── parsers/            # Tree-sitter language parsers
│   ├── handlers/       # Language-specific handlers (python.py, js_ts.py, etc.)
│   ├── class_ingest/   # Class relationship ingestion
│   └── py/, js_ts/, lua/, java/, cpp/, rs/
├── services/            # graph_service.py, llm.py, protobuf_service.py
├── tools/              # Agent tools (file_reader, shell_command, etc.)
├── providers/          # LLM providers (base.py, openai.py, etc.)
└── utils/              # path_utils, source_extraction, fqn_resolver
```

### Key Conventions
- **Logging**: Use `from loguru import logger` - `logger.info()`, `logger.error()`
- **Graph operations**: Use `MemgraphIngestor` from `graph_service.py`
- **Constants**: Import as `from . import constants as cs`
- **Configuration**: Use Pydantic `BaseSettings` from `config.py`
- **LLM Providers**: Implement `BaseProvider` interface in `providers/base.py`

## Testing

```bash
# Markers in pyproject.toml
pytest -m "not integration"           # Unit tests only
pytest -m "integration" -v            # Integration tests (requires Docker)
pytest -m "slow"                      # Slow tests (may download models)

# Parallel execution
pytest -n auto                        # Use all CPU cores
pytest -n 4                           # Use 4 workers
```

## Pre-commit Hooks
```bash
# Install
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg

# Run manually
make pre-commit
```

Checks run: ruff format → ruff check --fix → ty check → check-no-docs → bandit → pytest

## Commit Messages
- Format: `type: description` (single line)
- Types: `fix:`, `feat:`, `refactor:`, `docs:`, `test:`, `chore:`
- Example: `fix: resolve null pointer in call_processor.py`
