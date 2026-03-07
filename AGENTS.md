# Code-Graph-RAG Project Guidelines

## Project Overview

Code-Graph-RAG is a knowledge graph-based code analysis tool that uses tree-sitter for parsing multiple programming languages (Python, JavaScript, TypeScript, C++, C#, Java, Rust, Go, Scala, PHP, Lua).

## Code Conventions

### Python Style
- Use **Ruff** for linting and formatting
- Run `ruff check --fix` before committing
- Run `ruff format` to format code
- Use type hints everywhere possible

### No Docstrings or Inline Comments
- **CRITICAL**: This project does NOT allow module docstrings or inline comments
- All `#` comments are forbidden in Python files
- Exception: Allowed markers in `ALLOWED_COMMENT_MARKERS` (see constants.py):
  - `(H)` - Header markers
  - `type:` - Type annotations
  - `noqa` - Ruff disable comments
  - `pyright` - Pyright directives
  - `ty:` - Tytyping comments
  - `@@protoc` - Protocol buffer
  - `nosec` - Bandit

### Pre-commit Hooks
Always run pre-commit checks before committing:
```bash
# Run pre-commit hooks locally
git commit --allow-empty-message --no-edit
# Or install pre-commit
uv pip install pre-commit
pre-commit install
```

### Type Checking
- Use **Ty** for type checking: `ty check`
- Run `ty check --exclude codebase_rag/tests/` before committing

### Security
- Run **Bandit** for security checks: `bandit -r codebase_rag -ll`

### Commit Messages
- Use Conventional Commits format: `type: description`
- Examples: `fix:`, `feat:`, `refactor:`, `docs:`, `test:`
- Keep commit message on single line

## Development Guidelines

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest codebase_rag/tests/test_class_ingest.py
```

### Building
```bash
# Build the project
uv pip install -e .

# Build with PyInstaller
pyinstaller main.py
```

### Language Support
The project uses tree-sitter grammars for:
- Python (.py)
- JavaScript (.js, .jsx)
- TypeScript (.ts, .tsx)
- C++ (.cpp, .h, .hpp, etc.)
- C# (.cs)
- Java (.java)
- Rust (.rs)
- Go (.go)
- Scala (.scala, .sc)
- PHP (.php)
- Lua (.lua)

## Directory Structure

```
codebase_rag/
├── parsers/           # Code parsers for different languages
│   ├── class_ingest/  # Class/interface extraction
│   ├── call_processor.py
│   └── import_processor.py
├── services/          # Core services (graph, indexing)
├── constants.py       # Project constants
├── types_defs.py      # Type definitions
└── tests/            # Test files
```

## Common Commands

```bash
# Index a repository
python -m codebase_rag index /path/to/repo

# Query the graph
python -m codebase_rag query "your question"

# Start interactive mode
python -m codebase_rag
```

## Important Notes

1. **Never add inline comments** - Use descriptive variable names instead
2. **No module docstrings** - Don't add `"""module docstring"""` at the top of files
3. **Always run linting** - Ruff must pass before commit
4. **Type hints required** - All functions should have type annotations
5. **Test coverage** - Write tests for new features
