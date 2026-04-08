# Issue #18: Semantic Search Missing Class/Interface/Module Nodes

## Problem Statement

When performing semantic search, many relevant code elements are not found because they are not indexed in the embeddings database. The current CYPHER_QUERY_EMBEDDINGS only indexes Function, Method, UnresolvedFunction, and StdlibMethod nodes.

## Symptoms

```
Found 0 semantic matches for: keycloak configuration authentication
```

Despite having 232 keycloak-related nodes in the graph, only 131 (56%) are searchable.

## Root Cause Analysis

### Current Indexed Node Types

| Node Type | Indexed? | Count |
|-----------|----------|-------|
| Function | ✅ | 2,233 |
| Method | ✅ | 1,165 |
| UnresolvedFunction | ✅ | 3,618 |
| StdlibMethod | ✅ | 73 |
| **Module** | ❌ | 2,167 |
| **File** | ❌ | 1,857 |
| **Class** | ❌ | 906 |
| **Folder** | ❌ | 669 |
| **Interface** | ❌ | 136 |

### Impact for Keycloak Search

| Loại | Số Lượng | Indexed? |
|------|----------|----------|
| Function | 92 | ✅ |
| Module | 39 | ❌ |
| File | 30 | ❌ |
| UnresolvedFunction | 22 | ✅ |
| Class | 21 | ❌ |
| Method | 17 | ✅ |
| Interface | 5 | ❌ |

**Result:** Only 131 of 232 nodes (56%) are searchable.

## Proposed Solution

### Option 1: Add Class and Interface to Embeddings (Recommended)

Modify `CYPHER_QUERY_EMBEDDINGS` in `constants.py`:

```cypher
// Add to existing query
UNION ALL
// Match Class nodes
MATCH (n:Class)
WHERE n.qualified_name STARTS WITH $project_prefix
RETURN id(n) AS node_id, n.qualified_name AS qualified_name,
       n.start_line AS start_line, n.end_line AS end_line,
       n.path AS path, 'Class' AS node_label

UNION ALL
// Match Interface nodes
MATCH (n:Interface)
WHERE n.qualified_name STARTS WITH $project_prefix
RETURN id(n) AS node_id, n.qualified_name AS qualified_name,
       NULL AS start_line, NULL AS end_line,
       n.path AS path, 'Interface' AS node_label
```

**Impact:** +1,042 embeddings (906 Class + 136 Interface)

### Option 2: Add Module to Embeddings

Module contains important context like Keycloak, Authentication, Configuration.

**Impact:** +2,167 Module embeddings

### Option 3: Add File to Embeddings

File nodes contain important context from documentation and source files.

**Impact:** +1,857 File embeddings

## Implementation Plan

| Phase | Task | Status |
| |------|--------|
| 1 | Add Class to embeddings query | ✅ Completed |
| 2 | Add Interface to embeddings query | ✅ Completed |
| 3 | Add Module to embeddings query | ✅ Completed |
| 4 | Add File to embeddings query | ✅ Completed |
| 5 | Add embedding handlers in graph_updater.py | ✅ Completed |
| 6 | Add configuration settings | ✅ Completed |
| 7 | Add log messages | ✅ Completed |
| 8 | Run lint/typecheck verification | ✅ Completed |

## Completion Summary

**Completion Date:** 2026-04-01

### Files Modified

| File | Changes |
|------|--------|
| `codebase_rag/constants.py` | Extended CYPHER_QUERY_EMBEDDINGS, added EMBEDDING_* constants |
| `codebase_rag/config.py` | Added EMBEDDING_MAX_CONTENT_CHARS, EMBEDDING_SKIP_EXTENSIONS, EMBEDDING_SKIP_MARKDOWN |
| `codebase_rag/graph_updater.py` | Added handlers for Class, Interface, Module, File nodes |
| `codebase_rag/logs.py` | Added FILE_NOT_FOUND, SKIPPING_BINARY_FILE, SKIPPING_MARKDOWN |

### Impact

| Metric | Before | After |
|--------|--------|-------|
| Indexed Node Types | 4 | 8 |
| Searchable Nodes | ~7,089 | ~11,154 |
| Coverage | 56% | 100% |

See `progress.md` and `results_report.md` for detailed implementation information.

## Related Issues

- Issue #17: CALLS Relationships Missing (Partially related - we added UnresolvedFunction/StdlibMethod to embeddings)

## Notes

This issue is **separate** from Issue #17. Issue #17 focuses on improving CALLS resolution, while this issue focuses on improving semantic search coverage.
