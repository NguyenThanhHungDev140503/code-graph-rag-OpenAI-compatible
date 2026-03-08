# Issue #17 - Báo Cáo Chi Tiết

## Tóm Tắt

Báo cáo này ghi lại chi tiết các hoạt động và thay đổi đã thực hiện để giải quyết Issue #17: CALLS Relationships Missing trong graph database.

---

## 1. Vấn Đề Ban Đầu

### Triệu Chứng
- Graph database bị thiếu ~95% CALLS relationships
- Tree-sitter phát hiện ~4,782 function calls nhưng chỉ 181 được lưu vào graph (3.8% capture rate)
- Đặc biệt Function → Function calls bị thiếu hoàn toàn (0%)

### Thống Kê Trước Khi Fix

| Source | Target | Count | Percentage |
|--------|--------|-------|-------------|
| Module | StdlibMethod | 57 | 35% |
| Method | StdlibMethod | 55 | 34% |
| Module | Function | 42 | 26% |
| **Function** | **Function** | **0** | **0%** |

---

## 2. Nguyên Nhân Gốc (Root Causes)

### 2.1 Unresolved Calls Bị Skip (Nguyên Nhân Chính)
- **Vị trí:** `call_processor.py` dòng 726-727
- **Code cũ:** `else: continue` - Unresolved calls bị bỏ qua hoàn toàn
- **Tác động:** ~95% calls không được lưu vào graph

### 2.2 C# Call Query Giới Hạn
- Chỉ `member_expression` được detect
- Thiếu: `invocation_expression`, `object_creation_expression`, `element_access_expression`

### 2.3 Resolution Logic Thiếu Type Inference Cho C#
- C# sử dụng namespace-based Qualified Names (ví dụ: `System.IO.File`)
- Resolution tạo QN không khớp với function_registry (file-path based QN)
- Fuzzy fallback không hoạt động chính xác

### 2.4 C# Method Resolution Chưa Đầy Đủ
- `resolve_method_calls` chỉ handle stdlib calls
- Không handle instance method calls

### 2.5 CSharpTypeInferenceEngine Missing
- Java type inference đang được reuse cho C# (temporary workaround)
- C# có unique syntax không được xử lý:
  - LINQ expressions: `list.Where(x => x > 5)`
  - Properties: `obj.Property` (get/set)
  - Indexers: `this[int i]`
  - Async/await: `await Task.Run()`
  - Constructor calls: `new Class()`

---

## 3. Các Thay Đổi Đã Thực Hiện

### 3.1 Thêm NodeLabel.UNRESOLVED_FUNCTION

**File:** `codebase_rag/constants.py`

**Thay đổi:**
```python
# Thêm vào NodeLabel enum
class NodeLabel(StrEnum):
    STDLIB_CLASS = "StdlibClass"
    STDLIB_METHOD = "StdlibMethod"
    UNRESOLVED_FUNCTION = "UnresolvedFunction"  # (H) Added

# Thêm vào NODE_UNIQUE_KEY_MAP
NodeLabel.UNRESOLVED_FUNCTION: UniqueKeyType.QUALIFIED_NAME,
```

**Lý do:** Cần một node type mới để represent unresolved function calls trong graph.

---

### 3.2 Sửa call_processor.py - Lưu Unresolved Thay Vì Skip

**File:** `codebase_rag/parsers/call_processor.py`

**Thay đổi (dòng ~726):**
```python
# TRƯỚC:
else:
    continue  # SKIPPED!

# SAU:
else:
    # (H) Store unresolved call with estimated target instead of skipping
    # This ensures all detected calls are captured in the graph
    callee_type = cs.NodeLabel.UNRESOLVED_FUNCTION
    callee_qn = f"unresolved{cs.SEPARATOR_DOT}{module_qn}{cs.SEPARATOR_DOT}{call_name}"

    # Create the UnresolvedFunction node first
    self.ingestor.ensure_node_batch(
        cs.NodeLabel.UNRESOLVED_FUNCTION,
        {
            cs.KEY_QUALIFIED_NAME: callee_qn,
            cs.KEY_NAME: call_name,
            "estimated_module": module_qn,
            "resolution_status": "unresolved",
        },
    )
    logger.debug(
        ls.CALL_UNRESOLVED_SKIPPED.format(
            caller=caller_qn,
            call_name=call_name,
            estimated_target=callee_qn,
        )
    )
```

**Lý do:** Thay vì skip unresolved calls, giờ sẽ lưu chúng vào graph với estimated target.

---

### 3.3 Thêm Log Message

**File:** `codebase_rag/logs.py`

**Thay đổi:**
```python
CALL_UNRESOLVED = "Could not resolve call: {call_name}"
CALL_UNRESOLVED_SKIPPED = "Unresolved call stored: {caller} -> {call_name} (estimated: {estimated_target})"
```

**Lý do:** Cần log message mới để track unresolved calls được stored.

---

### 3.4 Fix Embeddings Cho UnresolvedFunction

**Vấn đề:** Embeddings query chỉ bao gồm Function và Method, không bao gồm UnresolvedFunction.

**3.4.1 File: `codebase_rag/constants.py`**

```python
# TRƯỚC:
CYPHER_QUERY_EMBEDDINGS = """
MATCH (m:Module)-[:DEFINES]->(n)
WHERE (n:Function OR n:Method)
...
"""

# SAU:
CYPHER_QUERY_EMBEDDINGS = """
// Match Function nodes defined by Module
MATCH (m:Module)-[:DEFINES]->(n:Function)
WHERE m.qualified_name STARTS WITH $project_prefix
RETURN id(n) AS node_id, n.qualified_name AS qualified_name,
       n.start_line AS start_line, n.end_line AS end_line,
       m.path AS path, 'Function' AS node_label

UNION ALL

// Match Method nodes defined by Module
MATCH (m:Module)-[:DEFINES]->(n:Method)
WHERE m.qualified_name STARTS WITH $project_prefix
RETURN id(n) AS node_id, n.qualified_name AS qualified_name,
       n.start_line AS start_line, n.end_line AS end_line,
       m.path AS path, 'Method' AS node_label

UNION ALL

// Match UnresolvedFunction nodes (no Module relationship needed)
MATCH (n:UnresolvedFunction)
RETURN id(n) AS node_id, n.qualified_name AS qualified_name,
       NULL AS start_line, NULL AS end_line,
       NULL AS path, 'UnresolvedFunction' AS node_label
"""
```

**3.4.2 File: `codebase_rag/types_defs.py`**

```python
# Thêm node_label vào EmbeddingQueryResult
class EmbeddingQueryResult(TypedDict):
    node_id: int
    qualified_name: str
    start_line: int | None
    end_line: int | None
    path: str | None
    node_label: str  # (H) Added for UnresolvedFunction handling
```

**3.4.3 File: `codebase_rag/graph_updater.py`**

```python
# Thêm xử lý UnresolvedFunction trong _generate_embeddings_for_project
def _generate_embeddings_for_project(self, ...):
    # ... existing code ...

    for row in results:
        parsed = self._parse_embedding_result(row)
        if not parsed:
            continue

        node_id = parsed[cs.KEY_NODE_ID]
        qualified_name = parsed[cs.KEY_QUALIFIED_NAME]
        node_label = parsed.get("node_label", "")

        # (H) Handle UnresolvedFunction nodes - generate synthetic source code
        if node_label == "UnresolvedFunction":
            # Generate synthetic source from qualified name for semantic search
            source_code = f"# Unresolved function call: {qualified_name}"
            try:
                embedding = embed_code(source_code)
                store_embedding(node_id, embedding, qualified_name)
                embedded_count += 1
            except Exception as e:
                logger.warning(
                    ls.EMBEDDING_FAILED.format(name=qualified_name, error=e)
                )
            continue

        # ... rest of existing code ...
```

**Lý do:** UnresolvedFunction nodes không có source code thực, cần generate synthetic source để tạo embeddings.

---

## 4. Kết Quả Đạt Được

### 4.1 CALLS Relationships

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Successful CALLS** | 523 | 12,124 | **23x increase** |
| **Failed CALLS** | 12,538 | 937 | 93% reduction |
| **Capture Rate** | 3.8% | 92.8% | ✅ ~95% target achieved |

### 4.2 Embeddings (Dự Kiến Sau Khi Re-run)

| Metric | Before | After (Estimated) |
|--------|--------|-------------------|
| **Total Embeddings** | 2,228 | ~14,000+ |
| **UnresolvedFunction Embeddings** | 0 | ~12,000+ |

### 4.3 Remaining Issues

**937 Failed Relationships cần investigate:**

| Loại Lỗi | Số Lượng | Nguyên Nhân |
|----------|----------|-------------|
| Caller missing (UnresolvedFunction) | 881 | Methods chưa được tạo trong graph |
| Method → Method | 27 | Caller methods missing |
| Method → StdlibMethod | 15 | Caller methods missing |
| Function.builtin.* | 14 | Built-in functions, no nodes |

**Root Cause:** Caller nodes (methods/functions) không được tạo trong graph - liên quan đến Issue #13 (C# Methods Not Created).

---

## 5. Các Files Thay Đổi

| File | Loại Thay Đổi | Mô Tả |
|------|---------------|-------|
| `codebase_rag/constants.py` | Modified | Thêm UNRESOLVED_FUNCTION, fix CYPHER_QUERY_EMBEDDINGS |
| `codebase_rag/logs.py` | Modified | Thêm CALL_UNRESOLVED_SKIPPED message |
| `codebase_rag/parsers/call_processor.py` | Modified | Lưu unresolved thay vì skip |
| `codebase_rag/types_defs.py` | Modified | Thêm node_label vào EmbeddingQueryResult |
| `codebase_rag/graph_updater.py` | Modified | Xử lý UnresolvedFunction embeddings |

---

## 6. Test Results

**Unit Tests:** ✅ Tất cả pass
- `test_call_processor.py`: 24 passed
- `test_call_resolver.py`: 19 passed

---

## 7. Phase Tiếp Theo

### Phase 2: CSharpTypeInferenceEngine (P1)

**Mục tiêu:** Đạt 80%+ resolution rate cho C#

**Các tasks cần làm:**

1. **Tạo C# Type Inference Engine**
   - File: `parsers/csharp/type_inference.py`
   - Class: `CSharpTypeInferenceEngine`

2. **Handle C# Specific Patterns**
   - LINQ expressions: `list.Where(x => x > 5)`
   - Properties: `obj.Property` (get/set)
   - Indexers: `this[int i]`
   - Async/await: `await Task.Run()`
   - Constructor calls: `new Class()`

3. **Integrate vào CallResolver**
   - Modify `type_inference.py` để route C# đến new engine
   - Update `resolve_csharp_method_call`

4. **Test**
   - Create test cases cho C# patterns
   - Benchmark resolution rate

### Phase 3: Re-resolve and Clean Graph (P2)

**Mục tiêu:** Clean graph với high confidence

**Options:**
1. Re-run resolution on stored unresolved calls
2. Query-time resolution

---

## 8. Tài Liệu Liên Quan

- Issue #17: CALLS Relationships Missing
- Issue #13: C# Methods Not Created (related)
- Plan: `issues/17/issue_17_resolution_plan.md`
- Progress: `issues/17/progress.md`

---

## 9. Version History

| Version | Ngày | Người | Mô Tả |
|---------|------|-------|-------|
| 1.0 | 2026-03-08 | Dev Team | Initial - Phase 1 Complete |

---

## 10. Appendix

### A. Code Snippets

#### A.1 UnresolvedFunction Node Creation
```python
self.ingestor.ensure_node_batch(
    cs.NodeLabel.UNRESOLVED_FUNCTION,
    {
        cs.KEY_QUALIFIED_NAME: callee_qn,
        cs.KEY_NAME: call_name,
        "estimated_module": module_qn,
        "resolution_status": "unresolved",
    },
)
```

#### A.2 Synthetic Source for Embeddings
```python
source_code = f"# Unresolved function call: {qualified_name}"
embedding = embed_code(source_code)
store_embedding(node_id, embedding, qualified_name)
```

### B. Configuration Changes

#### B.1 NodeLabel Addition
```python
class NodeLabel(StrEnum):
    # ... existing ...
    UNRESOLVED_FUNCTION = "UnresolvedFunction"
```

#### B.2 Unique Key Map Addition
```python
NodeLabel.UNRESOLVED_FUNCTION: UniqueKeyType.QUALIFIED_NAME,
```

---

**Last Updated:** 2026-03-08 15:30 UTC
**Author:** Development Team
**Version:** 1.0
