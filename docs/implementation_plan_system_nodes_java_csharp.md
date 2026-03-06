# Implementation Plan: System Nodes cho Java và C#

## 1. Mục tiêu

Chỉ implement System Nodes cho các ngôn ngữ **thuần OOP** có standard library rõ ràng và giới hạn:
- ✅ Java
- ✅ C#

**KHÔNG** implement cho:
- ❌ JavaScript/TypeScript (giữ nguyên behavior hiện tại - skip)
- ❌ Python (giữ nguyên - skip)
- ❌ Rust (giữ nguyên - skip)

## 2. Lý do

| Ngôn ngữ | Stdlib characteristics | Phù hợp System Nodes? |
|----------|----------------------|----------------------|
| **Java** | Well-defined, finite, OOP classes (`System`, `List`, `Optional`) | ✅ Yes |
| **C#** | Well-defined, finite, OOP classes (`Console`, `Enumerable`, `List<T>`) | ✅ Yes |
| **JavaScript** | Huge, dynamic, prototype-based, many ways to extend | ❌ No |
| **Python** | Many builtins, duck typing, harder to categorize | ❌ No |

Java và C# có đặc điểm:
- Standard library tập trung vào một số ít classes
- Methods rõ ràng, có documentation đầy đủ
- Ít callback patterns (so với JS)
- OOP hierarchy rõ ràng

## 3. Implementation Tasks

### Task 1: Thêm Constants cho Java

**File**: `codebase_rag/constants.py`

```python
# Thêm mới
JAVA_STDLIB_METHODS: dict[str, dict] = {
    # System I/O
    "System.out.println": {
        "category": "io",
        "module": "System.out",
        "has_side_effect": True,
        "is_static": True,
    },
    "System.out.print": {...},
    "System.out.printf": {...},
    "System.err.println": {...},
    "System.exit": {"category": "control_flow", "has_side_effect": True},

    # Collections Factory Methods
    "List.of": {"category": "factory", "has_side_effect": False},
    "List.copyOf": {"category": "factory", "has_side_effect": False},
    "Set.of": {"category": "factory", "has_side_effect": False},
    "Map.of": {"category": "factory", "has_side_effect": False},
    "Arrays.asList": {"category": "factory", "has_side_effect": False},
    "Arrays.stream": {"category": "factory", "has_side_effect": False},

    # Stream API - Higher Order
    "Stream.map": {"category": "higher_order", "accepts_callback": True},
    "Stream.filter": {"category": "higher_order", "accepts_callback": True},
    "Stream.reduce": {"category": "higher_order", "accepts_callback": True},
    "Stream.forEach": {"category": "higher_order", "accepts_callback": True},
    "Stream.anyMatch": {"category": "higher_order", "accepts_callback": True},
    "Stream.allMatch": {"category": "higher_order", "accepts_callback": True},
    "Stream.findFirst": {"category": "higher_order", "accepts_callback": False},

    # Optional
    "Optional.of": {"category": "factory", "has_side_effect": False},
    "Optional.ofNullable": {"category": "factory", "has_side_effect": False},
    "Optional.empty": {"category": "factory", "has_side_effect": False},
    "Optional.map": {"category": "higher_order", "accepts_callback": True},
    "Optional.flatMap": {"category": "higher_order", "accepts_callback": True},
    "Optional.orElse": {"category": "control_flow", "has_side_effect": False},

    # Objects
    "Objects.requireNonNull": {"category": "validation", "has_side_effect": False},
    "Objects.isNull": {"category": "pure", "has_side_effect": False},
    "Objects.nonNull": {"category": "pure", "has_side_effect": False},

    # String
    "String.valueOf": {"category": "pure", "has_side_effect": False},

    # Math
    "Math.abs": {"category": "pure", "has_side_effect": False},
    "Math.max": {"category": "pure", "has_side_effect": False},
    "Math.min": {"category": "pure", "has_side_effect": False},
    "Math.random": {"category": "pure", "has_side_effect": False},
}
```

### Task 2: Thêm Constants cho C#

**File**: `codebase_rag/constants.py`

```python
# Thêm mới
CSHARP_STDLIB_METHODS: dict[str, dict] = {
    # Console I/O
    "Console.WriteLine": {"category": "io", "module": "Console", "has_side_effect": True},
    "Console.Write": {"category": "io", "module": "Console", "has_side_effect": True},
    "Console.ReadLine": {"category": "io", "module": "Console", "has_side_effect": True},
    "Console.Read": {"category": "io", "module": "Console", "has_side_effect": True},

    # LINQ - Higher Order
    "Enumerable.Select": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.Where": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.First": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.FirstOrDefault": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.Any": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.All": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.Count": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.ToList": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.ToArray": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.Aggregate": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.OrderBy": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.GroupBy": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},

    # List<T> Methods
    "List<T>.Add": {"category": "mutation", "module": "List<T>", "has_side_effect": True},
    "List<T>.AddRange": {"category": "mutation", "module": "List<T>", "has_side_effect": True},
    "List<T>.Remove": {"category": "mutation", "module": "List<T>", "has_side_effect": True},
    "List<T>.ForEach": {"category": "higher_order", "module": "List<T>", "accepts_callback": True},
    "List<T>.Find": {"category": "higher_order", "module": "List<T>", "accepts_callback": True},
    "List<T>.FindAll": {"category": "higher_order", "module": "List<T>", "accepts_callback": True},
    "List<T>.Exists": {"category": "higher_order", "module": "List<T>", "accepts_callback": True},
    "List<T>.TrueForAll": {"category": "higher_order", "module": "List<T>", "accepts_callback": True},

    # Dictionary<TKey, TValue>
    "Dictionary<TKey, TValue>.Add": {"category": "mutation", "has_side_effect": True},
    "Dictionary<TKey, TValue>.ContainsKey": {"category": "pure", "has_side_effect": False},
    "Dictionary<TKey, TValue>.TryGetValue": {"category": "pure", "has_side_effect": False},

    # String
    "String.IsNullOrEmpty": {"category": "pure", "module": "String", "has_side_effect": False},
    "String.IsNullOrWhiteSpace": {"category": "pure", "module": "String", "has_side_effect": False},
    "String.Format": {"category": "pure", "module": "String", "has_side_effect": False},

    # DateTime
    "DateTime.Now": {"category": "pure", "module": "DateTime", "has_side_effect": False},
    "DateTime.UtcNow": {"category": "pure", "module": "DateTime", "has_side_effect": False},

    # Task (async)
    "Task.Run": {"category": "async", "module": "Task", "has_side_effect": False},
    "Task.FromResult": {"category": "factory", "module": "Task", "has_side_effect": False},
    "Task.WhenAll": {"category": "async", "module": "Task", "has_side_effect": False},
    "Task.WhenAny": {"category": "async", "module": "Task", "has_side_effect": False},

    # Enumerable (static)
    "Enumerable.Empty": {"category": "factory", "module": "Enumerable", "has_side_effect": False},
    "Enumerable.Range": {"category": "factory", "module": "Enumerable", "has_side_effect": False},
    "Enumerable.Repeat": {"category": "factory", "module": "Enumerable", "has_side_effect": False},
    "Enumerable.Concat": {"category": "factory", "module": "Enumerable", "has_side_effect": False},

    # Action & Func delegates
    "Action": {"category": "delegate", "module": "System", "has_side_effect": False},
    "Func<T, TResult>": {"category": "delegate", "module": "System", "has_side_effect": False},
}
```

### Task 3: Thêm NodeLabel mới

**File**: `codebase_rag/constants.py`

```python
class NodeLabel(StrEnum):
    # ... existing ...
    STDLIB_CLASS = "StdlibClass"      # Java: System, List, Optional; C#: Console, Enumerable
    STDLIB_METHOD = "StdlibMethod"    # System.out.println, Enumerable.Select
```

**Lưu ý**: Khi sử dụng `SupportedLanguage` trong `call_processor.py`, có thể dùng string literal type annotation (`"SupportedLanguage"`) để tránh circular import nếu cần.

### Task 4: Cập nhật CallResolver

**File**: `codebase_rag/parsers/call_resolver.py`

```python
def resolve_builtin_call(
    self,
    call_name: str,
    language: SupportedLanguage  # <-- THÊM MỚI: language parameter
) -> tuple[str, str] | None:
    """Resolve standard library methods for OOP languages."""

    # Java - thêm mới
    if language == SupportedLanguage.JAVA:
        if call_name in cs.JAVA_STDLIB_METHODS:
            metadata = cs.JAVA_STDLIB_METHODS[call_name]
            return (cs.NodeLabel.STDLIB_METHOD, f"java.stdlib.{call_name}")

    # C# - thêm mới
    elif language == SupportedLanguage.CSHARP:
        if call_name in cs.CSHARP_STDLIB_METHODS:
            metadata = cs.CSHARP_STDLIB_METHODS[call_name]
            return (cs.NodeLabel.STDLIB_METHOD, f"csharp.stdlib.{call_name}")

    # JavaScript/TypeScript - giữ nguyên behavior cũ
    elif language in (SupportedLanguage.JAVASCRIPT, SupportedLanguage.TYPESCRIPT):
        # Giữ nguyên logic hiện tại
        if call_name in cs.JS_BUILTIN_PATTERNS:
            return (cs.NodeLabel.FUNCTION, f"{cs.BUILTIN_PREFIX}.{call_name}")

        # Handle Function.prototype methods
        for suffix, method in cs.JS_FUNCTION_PROTOTYPE_SUFFIXES.items():
            if call_name.endswith(suffix):
                return (
                    cs.NodeLabel.FUNCTION,
                    f"{cs.BUILTIN_PREFIX}{cs.SEPARATOR_DOT}Function{cs.SEPARATOR_PROTOTYPE}{method}",
                )

    return None
```

### Task 5: Cập nhật CallProcessor

**File**: `codebase_rag/parsers/call_processor.py`

```python
def __init__(self, ...) -> None:
    # ... existing ...
    self._created_stdlib_nodes: set[str] = set()  # <-- THÊM MỚI
    self._created_stdlib_classes: set[str] = set()  # <-- THÊM MỚI

def _ingest_function_calls(self, caller_node, caller_qn, caller_type, class_context, module_qn, language, queries):
    # ... existing code đến line 357 ...

    # Sau khi thử resolve_function_call và resolve_java_method_call
    # Thêm language parameter vào resolve_builtin_call
    elif builtin_info := self._resolver.resolve_builtin_call(call_name, language):  # <-- SỬA: thêm language param
        callee_type, callee_qn = builtin_info

        # Java/C#: Tạo stdlib nodes và relationships
        if language in (cs.SupportedLanguage.JAVA, cs.SupportedLanguage.CSHARP):
            self._ensure_stdlib_node(callee_qn, call_name, language)
            self.ingestor.ensure_relationship_batch(
                (caller_type, cs.KEY_QUALIFIED_NAME, caller_qn),
                cs.RelationshipType.CALLS,
                (callee_type, cs.KEY_QUALIFIED_NAME, callee_qn),
            )
        # JavaScript/TypeScript: giữ nguyên behavior cũ (vẫn skip)
        elif language in (cs.SupportedLanguage.JAVASCRIPT, cs.SupportedLanguage.TYPESCRIPT):
            # JS/TS: không tạo node, chỉ add relationship nếu cần
            # Hoặc continue để skip hoàn toàn như hiện tại
            continue

        continue  # <-- THÊM: để tránh xử lý tiếp
```

**Lưu ý**: Trong codebase hiện tại, `language` đã được truyền vào `_ingest_function_calls`, nên chỉ cần forward nó xuống `resolve_builtin_call`.

### Task 6: Thêm method `_ensure_stdlib_node`

**File**: `codebase_rag/parsers/call_processor.py`

```python
def _ensure_stdlib_node(
    self,
    stdlib_qn: str,
    call_name: str,
    language: "SupportedLanguage"  # <-- THÊM MỚI: type annotation với string literal để tránh circular import
) -> None:
    """Ensure a stdlib method node exists in the graph."""
    if stdlib_qn in self._created_stdlib_nodes:
        return

    # Get metadata từ constants
    if language == cs.SupportedLanguage.JAVA:
        metadata = cs.JAVA_STDLIB_METHODS.get(call_name, {})
    elif language == cs.SupportedLanguage.CSHARP:
        metadata = cs.CSHARP_STDLIB_METHODS.get(call_name, {})
    else:
        return

    # Determine class name from call_name (e.g., "System.out.println" -> "System")
    class_name = call_name.split('.')[0]
    prefix = "java" if language == cs.SupportedLanguage.JAVA else "csharp"
    class_qn = f"{prefix}.stdlib.{class_name}"

    # Create class node if not exists
    if class_qn not in self._created_stdlib_classes:
        self.ingestor.ensure_node_batch(
            cs.NodeLabel.STDLIB_CLASS,
            {
                cs.KEY_QUALIFIED_NAME: class_qn,
                cs.KEY_NAME: class_name,
                "language": language.value,
            },
        )
        self._created_stdlib_classes.add(class_qn)

    # Create method node
    self.ingestor.ensure_node_batch(
        cs.NodeLabel.STDLIB_METHOD,
        {
            cs.KEY_QUALIFIED_NAME: stdlib_qn,
            cs.KEY_NAME: call_name,
            "category": metadata.get("category", "unknown"),
            "has_side_effect": metadata.get("has_side_effect", None),
            "accepts_callback": metadata.get("accepts_callback", False),
        },
    )

    # Create relationship: StdlibClass --DEFINES--> StdlibMethod
    self.ingestor.ensure_relationship_batch(
        (cs.NodeLabel.STDLIB_CLASS, cs.KEY_QUALIFIED_NAME, class_qn),
        cs.RelationshipType.DEFINES,
        (cs.NodeLabel.STDLIB_METHOD, cs.KEY_QUALIFIED_NAME, stdlib_qn),
    )

    self._created_stdlib_nodes.add(stdlib_qn)
```

## 4. Graph Structure

```
Java Example:
┌─────────────────────┐     CALLS     ┌─────────────────────────┐
│ UserClass:Process   │──────────────▶│ StdlibMethod:           │
│                     │               │ java.stdlib.System.out  │
└─────────────────────┘               │ .println               │
                                       │ category: io           │
                                       │ has_side_effect: true  │
                                       └────────────────────────┘
                                              ▲
                                              │ DEFINES
                                       ┌──────┴──────────┐
                                       │ StdlibClass:    │
                                       │ java.stdlib.System
                                       └─────────────────┘

C# Example:
┌─────────────────────┐     CALLS     ┌─────────────────────────┐
│ UserClass:Handler   │──────────────▶│ StdlibMethod:           │
│                     │               │ csharp.stdlib.Console   │
                                       │ .WriteLine             │
                                       │ category: io           │
                                       └────────────────────────┘
                                              ▲
                                              │ DEFINES
                                       ┌──────┴──────────┐
                                       │ StdlibClass:    │
                                       │ csharp.stdlib.Console
                                       └─────────────────┘
```

## 5. Example Queries

```cypher
-- Java: Tìm tất cả methods gọi System.out.println
MATCH (m:Method)-[:CALLS]->(s:StdlibMethod {name: 'System.out.println'})
WHERE s.language = 'java'
RETURN m.qualified_name

-- C#: Tìm tất cả methods dùng LINQ Select
MATCH (m:Method)-[:CALLS]->(s:StdlibMethod)
WHERE s.name STARTS WITH 'Enumerable.Select'
RETURN m.qualified_name, s.name

-- Java: Impact analysis - ai dùng Stream API
MATCH (m:Method)-[:CALLS]->(s:StdlibMethod)
WHERE s.name STARTS WITH 'Stream.'
RETURN m.qualified_name, collect(s.name) as stream_operations

-- C#: Async methods dùng Task.WhenAll
MATCH (m:Method)-[:CALLS]->(s:StdlibMethod {name: 'Task.WhenAll'})
RETURN m.qualified_name
```

## 6. Files cần thay đổi

| File | Thay đổi |
|------|----------|
| `codebase_rag/constants.py` | Thêm `JAVA_STDLIB_METHODS`, `CSHARP_STDLIB_METHODS`, `NodeLabel.STDLIB_CLASS`, `NodeLabel.STDLIB_METHOD` |
| `codebase_rag/parsers/call_resolver.py` | 1. Thêm `language: SupportedLanguage` param vào `resolve_builtin_call()` 2. Thêm logic xử lý Java/C# |
| `codebase_rag/parsers/call_processor.py` | 1. Thêm `_ensure_stdlib_node()` method 2. Thêm `language` param khi gọi `resolve_builtin_call()` |

## 7. Kiểm tra signature hiện tại trước khi implement

**Bước quan trọng**: Trước khi implement, cần kiểm tra signature thực tế của các methods trong codebase:

### CallResolver.resolve_builtin_call()
```python
# Xem file: codebase_rag/parsers/call_resolver.py (khoảng line 488)
def resolve_builtin_call(self, call_name: str) -> tuple[str, str] | None:
```

### CallProcessor._ingest_function_calls()
```python
# Xem file: codebase_rag/parsers/call_processor.py (khoảng line 351)
# Tìm đoạn gọi resolve_builtin_call và thêm language parameter
elif builtin_info := self._resolver.resolve_builtin_call(call_name):
```

### CallProcessor.__init__()
```python
# Kiểm tra xem đã có _created_stdlib_nodes chưa
# Nếu chưa, cần thêm vào __init__
```

## 8. Backward Compatibility

- ✅ JavaScript/TypeScript: **Không thay đổi** - giữ nguyên skip behavior
- ✅ Python/Rust: **Không thay đổi** - giữ nguyên skip behavior
- ✅ Java: **Thêm mới** - System Nodes
- ✅ C#: **Thêm mới** - System Nodes

## 9. Review Points

1. **List methods đầy đủ?** - Cần review kỹ hơn các methods phổ biến
2. **Naming convention nhất quán?** - `java.stdlib.` vs `csharp.stdlib.`
3. **Category enum?** - Có thể thêm `BuiltinCategory` cho consistent
4. **Config option?** - Có thể thêm flag để enable/disable per language
