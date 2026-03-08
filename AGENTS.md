# Code-Graph-RAG Project Guidelines

## Project Overview

Code-Graph-RAG is a knowledge graph-based code analysis tool that uses tree-sitter for parsing multiple programming languages (Python, JavaScript, TypeScript, C++, C#, Java, Rust, Go, Scala, PHP, Lua). The system builds a comprehensive knowledge graph using Memgraph and enables natural language querying of codebase structure and relationships.

## Architecture

The system consists of two main components:

1. **Multi-language Parser**: Tree-sitter based parsing system that analyzes codebases and ingests data into Memgraph
2. **RAG System** (`codebase_rag/`): Interactive CLI for querying the stored knowledge graph

## Detailed Component Analysis

### Core Entry Points

| File | Description |
|------|-------------|
| `main.py` | Main entry point for interactive CLI, optimization loop, and agent orchestration |
| `cli.py` | Command line interface using Typer |
| `cli_help.py` | CLI help text and messages |

### Core Modules

| File | Description |
|------|-------------|
| `config.py` | Configuration management using Pydantic Settings, environment variables, model configs |
| `constants.py` | Project constants (colors, styles, UI messages, settings) - 93KB |
| `types_defs.py` | Type definitions for the entire project |
| `models.py` | Data models (SessionState, AppContext, GraphNode, GraphRelationship, LanguageSpec) |
| `prompts.py` | AI prompts for orchestration and optimization |
| `exceptions.py` | Custom exceptions |
| `decorators.py` | Decorators for the project |
| `logs.py` | Logging configuration and messages |

### Graph & Data Management

| File | Description |
|------|-------------|
| `graph_service.py` | MemgraphIngestor - handles connection to Memgraph database, batch operations, graph export |
| `graph_loader.py` | Load graph data from JSON exports |
| `graph_updater.py` | Real-time graph updates when code changes |
| `embedder.py` | Embedding utilities |
| `unixcoder.py` | UniXcoder model for semantic code search |
| `vector_store.py` | Qdrant vector store for semantic search |

### Language Support

| File | Description |
|------|-------------|
| `language_spec.py` | Language specifications and configurations |
| `language.py` | Language management tools (add/remove grammars) |

### Parsers (`codebase_rag/parsers/`)

The parser system is divided into multiple components:

**Core Processors:**
| File | Description |
|------|-------------|
| `call_processor.py` | Process function calls and build CALLS relationships |
| `call_resolver.py` | Resolve function call relationships across files |
| `import_processor.py` | Process imports and build IMPORTS/EXPORTS relationships |
| `dependency_parser.py` | Parse pyproject.toml to extract external dependencies |
| `definition_processor.py` | Process definitions (functions, classes) |
| `function_ingest.py` | Function ingestion logic |
| `structure_processor.py` | Process folder/file structure |
| `type_inference.py` | Type inference utilities |
| `stdlib_extractor.py` | Extract standard library information |
| `factory.py` | Factory for creating language-specific parsers |

**Language-Specific Handlers (`handlers/`):**
| File | Description |
|------|-------------|
| `python.py` | Python language handler |
| `js_ts.py` | JavaScript/TypeScript handler |
| `java.py` | Java language handler |
| `cpp.py` | C++ language handler |
| `rust.py` | Rust language handler |
| `lua.lua` | Lua language handler |
| `protocol.py` | Protocol buffer handler |

**Language-Specific Parsers:**
| Directory | Description |
|-----------|-------------|
| `py/` | Python-specific parsing (AST analysis, type inference, variable analysis) |
| `js_ts/` | JavaScript/TypeScript parsing |
| `lua/` | Lua parsing |
| `java/` | Java parsing |
| `cpp/` | C++ parsing |
| `rs/` | Rust parsing |

**Class Ingestion (`class_ingest/`):**
| File | Description |
|------|-------------|
| `__init__.py` | Class ingestion initialization |
| `identity.py` | Class identity handling |
| `relationships.py` | Class relationships (INHERITS, IMPLEMENTS) |
| `parent_extraction.py` | Extract parent classes |
| `mixin.py` | Mixin detection |
| `method_override.py` | Method override detection |
| `node_type.py` | Node type definitions |
| `cpp_modules.py` | C++ module handling |
| `utils.py` | Utility functions |

### Services (`codebase_rag/services/`)

| File | Description |
|------|-------------|
| `graph_service.py` | Memgraph database operations, ingestion, export |
| `llm.py` | LLM integration and Cypher query generation |
| `protobuf_service.py` | Protocol buffer handling |

### Tools (`codebase_rag/tools/`)

Agent tools for interacting with the codebase:

| File | Description |
|------|-------------|
| `codebase_query.py` | Query the knowledge graph using natural language |
| `code_retrieval.py` | Retrieve source code snippets |
| `file_reader.py` | Read files with pagination |
| `file_writer.py` | Create new files |
| `file_editor.py` | Surgical code replacement |
| `shell_command.py` | Execute shell commands (sandboxed) |
| `directory_lister.py` | List directory contents |
| `document_analyzer.py` | Analyze documents (PDFs, images) |
| `semantic_search.py` | Semantic code search using embeddings |
| `health_checker.py` | Health check utilities |
| `tool_descriptions.py` | Tool descriptions for MCP |

### MCP Server (`codebase_rag/mcp/`)

| File | Description |
|------|-------------|
| `server.py` | MCP server implementation |
| `tools.py` | MCP tool definitions and handlers |

### Providers (`codebase_rag/providers/`)

| File | Description |
|------|-------------|
| `base.py` | Base provider interface for LLM integration (Google, OpenAI, Ollama) |

### Utilities (`codebase_rag/utils/`)

| File | Description |
|------|-------------|
| `path_utils.py` | Path manipulation utilities |
| `source_extraction.py` | Extract source code from AST |
| `dependencies.py` | Dependency analysis utilities |
| `fqn_resolver.py` | Fully qualified name resolution |

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

### Graph Export
Export the knowledge graph to JSON for programmatic access:

```bash
# Export graph to JSON file
uv run cgr export -o my_graph.json

# Export with custom batch size
uv run cgr export -o my_graph.json --batch-size 5000
```

Using exported data:
```python
from codebase_rag.graph_loader import load_graph

# Load the exported graph
graph = load_graph("my_graph.json")

# Get summary statistics
summary = graph.summary()
print(f"Total nodes: {summary['total_nodes']}")
print(f"Total relationships: {summary['total_relationships']}")

# Find specific node types
functions = graph.find_nodes_by_label("Function")
classes = graph.find_nodes_by_label("Class")

# Analyze relationships
for func in functions[:5]:
    relationships = graph.get_relationships_for_node(func.node_id)
    print(f"Function {func.properties['name']} has {len(relationships)} relationships")
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
