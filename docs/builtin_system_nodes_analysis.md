# Phân tích giải pháp Include Builtins as System Nodes trong Call Graph

## 1. Hiện trạng (Current State)

Codebase hiện tại xử lý builtins theo kiểu **skip hoàn toàn**:

```
call_processor._ingest_function_calls:
  call_name → resolve_function_call → ❌ fail
                → resolve_builtin_call → ✅ match → continue (SKIP)
                → resolve_cpp_operator_call → ...

  Hoặc: callee_qn.startswith("builtin.") → continue (SKIP)
```

Điều này nghĩa là trong graph, **không có bất kỳ trace nào** cho thấy function A gọi `console.log` hay `Array.prototype.map`. Thông tin hoàn toàn bị mất.

### Đoạn code xử lý hiện tại trong `call_processor.py`

```python
# Lines 351-373 trong call_processor.py
elif self._resolver.resolve_builtin_call(call_name):
    # (H) Skip builtin calls - no nodes exist in graph for builtins
    continue
# ...
# (H) Skip calls to builtin functions - no nodes exist in graph
if isinstance(callee_qn, str) and callee_qn.startswith(
    f"{cs.BUILTIN_PREFIX}{cs.SEPARATOR_DOT}"
):
    continue
```

## 2. Vấn đề của việc skip hoàn toàn

| Vấn đề | Ví dụ cụ thể | Impact |
|--------|-------------|--------|
| **Mất context về behavior** | `processData()` gọi `console.log` → biết nó có side-effect (I/O) | Không nhận diện được functions có side-effects |
| **Mất dependency chain qua callbacks** | `items.map(transform)` → relationship giữa caller và `transform` bị mất | Incomplete call graph cho higher-order functions |
| **Không phân biệt được function "tính toán thuần" vs "có side-effect"** | `Math.random()` vs `fetch()` vs `setTimeout()` | Impact analysis thiếu chính xác |
| **RAG query mất context** | Hỏi "Hàm nào gọi console.log?" → không trả lời được | Giảm chất lượng RAG |
| **Refactoring blind spots** | Muốn thay `setTimeout` → `queueMicrotask` → không biết ai dùng | Refactoring risk |

## 3. Giải pháp đề xuất: System Nodes

### 3.1 Mô hình Graph mới

```
Hiện tại:
  [Function: processData] --CALLS--> ??? (mất)

Đề xuất:
  [Function: processData] --CALLS--> [Builtin: console.log]
  [Function: processData] --CALLS--> [Builtin: Array.prototype.map]
  [Function: fetchUser]   --CALLS--> [Builtin: JSON.parse]

  Builtin nodes thuộc về:
  [BuiltinModule: console] --DEFINES--> [Builtin: console.log]
  [BuiltinModule: Array]   --DEFINES--> [Builtin: Array.prototype.map]
  [BuiltinModule: JSON]    --DEFINES--> [Builtin: JSON.parse]
```

### 3.2 Thay đổi Constants

Thêm vào file `constants.py`:

```python
class NodeLabel(StrEnum):
    # ... existing labels ...
    BUILTIN_MODULE = "BuiltinModule"   # console, Math, JSON, Array, ...
    BUILTIN_FUNCTION = "BuiltinFunction"  # console.log, Math.floor, ...

class RelationshipType(StrEnum):
    # ... existing ...
    # Giữ nguyên CALLS vì semantic không đổi
    # Chỉ cần phân biệt qua node type

# Builtin classification
class BuiltinCategory(StrEnum):
    PURE = "pure"           # Math.floor, parseInt - no side effects
    IO = "io"               # console.log, fetch - I/O side effects
    ASYNC = "async"         # setTimeout, Promise.then - async behavior
    MUTATION = "mutation"   # Array.prototype.push, Object.assign - mutates data
    HIGHER_ORDER = "higher_order"  # map, filter, reduce - accepts callbacks
```

### 3.3 Metadata cho Builtin Nodes

```python
# Properties cho mỗi builtin node
BUILTIN_METADATA = {
    # Console methods - IO category
    "console.log": {
        "category": BuiltinCategory.IO,
        "module": "console",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "console.error": {
        "category": BuiltinCategory.IO,
        "module": "console",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "console.warn": {
        "category": BuiltinCategory.IO,
        "module": "console",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },

    # Array methods - Higher-order category
    "Array.prototype.map": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Array.prototype.filter": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Array.prototype.reduce": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Array.prototype.forEach": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": True,  # forEach can have side effects in callback
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Array.prototype.find": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Array.prototype.findIndex": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Array.prototype.some": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Array.prototype.every": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Array.prototype.push": {
        "category": BuiltinCategory.MUTATION,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "Array.prototype.pop": {
        "category": BuiltinCategory.MUTATION,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "Array.prototype.splice": {
        "category": BuiltinCategory.MUTATION,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": True,
        "accepts_callback": False,
    },

    # Async - Async category
    "setTimeout": {
        "category": BuiltinCategory.ASYNC,
        "module": "global",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "setInterval": {
        "category": BuiltinCategory.ASYNC,
        "module": "global",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Promise.prototype.then": {
        "category": BuiltinCategory.ASYNC,
        "module": "Promise",
        "is_deterministic": False,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Promise.prototype.catch": {
        "category": BuiltinCategory.ASYNC,
        "module": "Promise",
        "is_deterministic": False,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Promise.prototype.finally": {
        "category": BuiltinCategory.ASYNC,
        "module": "Promise",
        "is_deterministic": False,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "fetch": {
        "category": BuiltinCategory.ASYNC,
        "module": "global",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },

    # Math - Pure category
    "Math.floor": {
        "category": BuiltinCategory.PURE,
        "module": "Math",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Math.ceil": {
        "category": BuiltinCategory.PURE,
        "module": "Math",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Math.round": {
        "category": BuiltinCategory.PURE,
        "module": "Math",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Math.random": {
        "category": BuiltinCategory.PURE,
        "module": "Math",
        "is_deterministic": False,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Math.min": {
        "category": BuiltinCategory.PURE,
        "module": "Math",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Math.max": {
        "category": BuiltinCategory.PURE,
        "module": "Math",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },

    # Global functions - Pure category
    "parseInt": {
        "category": BuiltinCategory.PURE,
        "module": "global",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "parseFloat": {
        "category": BuiltinCategory.PURE,
        "module": "global",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "isNaN": {
        "category": BuiltinCategory.PURE,
        "module": "global",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "isFinite": {
        "category": BuiltinCategory.PURE,
        "module": "global",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },

    # JSON - Pure category
    "JSON.parse": {
        "category": BuiltinCategory.PURE,
        "module": "JSON",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "JSON.stringify": {
        "category": BuiltinCategory.PURE,
        "module": "JSON",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },

    # Object methods - Mixed
    "Object.keys": {
        "category": BuiltinCategory.PURE,
        "module": "Object",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Object.values": {
        "category": BuiltinCategory.PURE,
        "module": "Object",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Object.entries": {
        "category": BuiltinCategory.PURE,
        "module": "Object",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Object.assign": {
        "category": BuiltinCategory.MUTATION,
        "module": "Object",
        "is_deterministic": True,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "Object.create": {
        "category": BuiltinCategory.PURE,
        "module": "Object",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Object.freeze": {
        "category": BuiltinCategory.MUTATION,
        "module": "Object",
        "is_deterministic": True,
        "has_side_effect": True,
        "accepts_callback": False,
    },

    # String methods - Pure (mostly)
    "String.prototype.split": {
        "category": BuiltinCategory.PURE,
        "module": "String",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "String.prototype.replace": {
        "category": BuiltinCategory.PURE,
        "module": "String",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "String.prototype.trim": {
        "category": BuiltinCategory.PURE,
        "module": "String",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "String.prototype.toLowerCase": {
        "category": BuiltinCategory.PURE,
        "module": "String",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "String.prototype.toUpperCase": {
        "category": BuiltinCategory.PURE,
        "module": "String",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },

    # RegExp
    "RegExp": {
        "category": BuiltinCategory.PURE,
        "module": "RegExp",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "String.prototype.match": {
        "category": BuiltinCategory.PURE,
        "module": "String",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "String.prototype.test": {
        "category": BuiltinCategory.PURE,
        "module": "RegExp",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },

    # Type checking
    "typeof": {
        "category": BuiltinCategory.PURE,
        "module": "global",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "instanceof": {
        "category": BuiltinCategory.PURE,
        "module": "global",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },

    # Array constructors and static methods
    "Array.isArray": {
        "category": BuiltinCategory.PURE,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Array.from": {
        "category": BuiltinCategory.PURE,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Array.of": {
        "category": BuiltinCategory.PURE,
        "module": "Array",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },

    # Map/Set
    "Map": {
        "category": BuiltinCategory.PURE,
        "module": "Map",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Set": {
        "category": BuiltinCategory.PURE,
        "module": "Set",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Map.prototype.forEach": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Map",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },
    "Set.prototype.forEach": {
        "category": BuiltinCategory.HIGHER_ORDER,
        "module": "Set",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": True,
        "callback_param_index": 0,
    },

    # Date
    "Date": {
        "category": BuiltinCategory.PURE,
        "module": "Date",
        "is_deterministic": False,  # Date.now() is non-deterministic
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "Date.now": {
        "category": BuiltinCategory.PURE,
        "module": "Date",
        "is_deterministic": False,
        "has_side_effect": False,
        "accepts_callback": False,
    },

    # Error
    "Error": {
        "category": BuiltinCategory.PURE,
        "module": "Error",
        "is_deterministic": True,
        "has_side_effect": False,
        "accepts_callback": False,
    },
    "throw": {
        "category": BuiltinCategory.IO,
        "module": "global",
        "is_deterministic": True,
        "has_side_effect": True,
        "accepts_callback": False,
    },

    # require (Node.js)
    "require": {
        "category": BuiltinCategory.ASYNC,
        "module": "global",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },

    # console methods extended
    "console.info": {
        "category": BuiltinCategory.IO,
        "module": "console",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "console.debug": {
        "category": BuiltinCategory.IO,
        "module": "console",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "console.table": {
        "category": BuiltinCategory.IO,
        "module": "console",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "console.time": {
        "category": BuiltinCategory.IO,
        "module": "console",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },
    "console.trace": {
        "category": BuiltinCategory.IO,
        "module": "console",
        "is_deterministic": False,
        "has_side_effect": True,
        "accepts_callback": False,
    },
}
```

## 4. Thay đổi trong `call_processor.py`

### 4.1 Constructor - Khởi tạo tracking sets

```python
class CallProcessor:
    def __init__(self, ...) -> None:
        # ... existing init code ...

        # Track created builtin nodes to avoid duplicates
        self._created_builtin_nodes: set[str] = set()
        self._created_builtin_modules: set[str] = set()
```

### 4.2 `_ingest_function_calls` - THAY ĐỔI CHÍNH

```python
# TRƯỚC (skip hoàn toàn):
elif self._resolver.resolve_builtin_call(call_name):
    continue  # ← Mất hoàn toàn
elif callee_qn.startswith(f"{cs.BUILTIN_PREFIX}{cs.SEPARATOR_DOT}"):
    continue  # ← Mất hoàn toàn

# SAU (include as system node):
elif builtin_info := self._resolver.resolve_builtin_call(call_name):
    callee_type, callee_qn = builtin_info
    # Tạo builtin node nếu chưa tồn tại + relationship
    self._ensure_builtin_node(callee_qn, call_name)
    self.ingestor.ensure_relationship_batch(
        (caller_type, cs.KEY_QUALIFIED_NAME, caller_qn),
        cs.RelationshipType.CALLS,
        (cs.NodeLabel.BUILTIN_FUNCTION, cs.KEY_QUALIFIED_NAME, callee_qn),
    )
    continue  # Skip thêm resolve_cpp_operator_call
```

### 4.3 Method mới `_ensure_builtin_node`

```python
def _ensure_builtin_node(self, builtin_qn: str, call_name: str) -> None:
    """Ensure a builtin function node exists in the graph as a system node."""
    if builtin_qn in self._created_builtin_nodes:
        return  # Đã tạo rồi, tránh duplicate

    metadata = cs.BUILTIN_METADATA.get(call_name, {})

    self.ingestor.ensure_node_batch(
        cs.NodeLabel.BUILTIN_FUNCTION,
        {
            cs.KEY_QUALIFIED_NAME: builtin_qn,
            cs.KEY_NAME: call_name,
            "category": metadata.get("category", "unknown"),
            "is_deterministic": metadata.get("is_deterministic", None),
            "has_side_effect": metadata.get("has_side_effect", None),
            "accepts_callback": metadata.get("accepts_callback", False),
        },
    )

    # Tạo builtin module node nếu cần
    module_name = metadata.get("module", call_name.split(".")[0])
    module_qn = f"{cs.BUILTIN_PREFIX}.{module_name}"

    if module_qn not in self._created_builtin_modules:
        self.ingestor.ensure_node_batch(
            cs.NodeLabel.BUILTIN_MODULE,
            {
                cs.KEY_QUALIFIED_NAME: module_qn,
                cs.KEY_NAME: module_name,
            },
        )
        self._created_builtin_modules.add(module_qn)

    # BuiltinModule --DEFINES--> BuiltinFunction
    self.ingestor.ensure_relationship_batch(
        (cs.NodeLabel.BUILTIN_MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
        cs.RelationshipType.DEFINES,
        (cs.NodeLabel.BUILTIN_FUNCTION, cs.KEY_QUALIFIED_NAME, builtin_qn),
    )

    self._created_builtin_nodes.add(builtin_qn)
```

## 5. Graph Structure hình thành

```
                          ┌──────────────────────┐
                          │ BuiltinModule: console│
                          └──────────┬───────────┘
                                     │ DEFINES
                                     ▼
┌─────────────────────┐    ┌─────────────────────────┐
│ Function: logUser   │───▶│ BuiltinFunction:         │
│ (user code)         │CALLS│ console.log             │
└─────────────────────┘    │ category: io             │
                           │ has_side_effect: true     │
                           └─────────────────────────┘

┌─────────────────────┐    ┌─────────────────────────┐
│ Function: transform │───▶│ BuiltinFunction:         │
│ (user code)         │CALLS│ Array.prototype.map     │
└─────────────────────┘    │ category: higher_order   │
                           │ accepts_callback: true    │
                           └─────────────────────────┘
                                     ▲
                                     │ DEFINES
                          ┌──────────┴───────────┐
                          │ BuiltinModule: Array  │
                          └──────────────────────┘
```

## 6. Lợi ích cụ thể cho RAG Queries

| Query | Trước (skip) | Sau (system nodes) |
|-------|-------------|-------------------|
| "Hàm nào gọi console.log?" | ❌ Không trả lời được | ✅ List tất cả callers |
| "Function nào có side-effect?" | ❌ Không biết | ✅ Traverse CALLS → BuiltinFunction(has_side_effect=true) |
| "Code nào dùng async APIs?" | ❌ Phải grep source | ✅ CALLS → BuiltinFunction(category=async) |
| "Impact nếu thay setTimeout?" | ❌ Blind spot | ✅ Reverse traverse từ BuiltinFunction |
| "Hàm nào pure?" | ❌ Không biết | ✅ Functions chỉ CALLS → BuiltinFunction(pure) hoặc user functions |
| "Map nào dùng callbacks?" | ❌ Mất chain | ✅ BuiltinFunction(accepts_callback=true) → trace callback |

### Ví dụ Cypher Queries

```cypher
-- Tìm tất cả functions gọi console.log
MATCH (f:Function)-[:CALLS]->(b:BuiltinFunction {name: 'console.log'})
RETURN f.qualified_name

-- Tìm functions có side-effect (gọi I/O)
MATCH (f:Function)-[:CALLS]->(b:BuiltinFunction)
WHERE b.has_side_effect = true
RETURN f.qualified_name, collect(b.name) as side_effects

-- Tìm tất cả async calls
MATCH (f:Function)-[:CALLS]->(b:BuiltinFunction)
WHERE b.category = 'async'
RETURN f.qualified_name, b.name

-- Tìm callback chains
MATCH (f:Function)-[:CALLS]->(b:BuiltinFunction {accepts_callback: true})-[:CALLS]->(callback:Function)
RETURN f.name as caller, callback.name as callback

-- Impact analysis: ai dùng setTimeout
MATCH (f:Function)-[:CALLS]->(b:BuiltinFunction {name: 'setTimeout'})
RETURN f.qualified_name
```

## 7. Performance Impact Analysis

```
Ước tính cho 1 project trung bình (~500 files JS/TS):

Số builtin calls trung bình: ~2000-5000 calls
Số unique builtin functions: ~30-50 unique
Số builtin modules: ~10-15

Graph size thay đổi:
  Nodes tăng: +30-50 (BuiltinFunction) + 10-15 (BuiltinModule) = ~50-65 nodes
  Relationships tăng: +2000-5000 (CALLS) + 50 (DEFINES) = ~2000-5050 rels

So với tổng graph thông thường:
  Nodes hiện tại: ~5000-15000 → tăng <1%
  Relationships hiện tại: ~10000-30000 → tăng ~10-16%

→ Relationship tăng đáng kể nhưng node tăng rất ít (vì deduplicate)
```

### Cách kiểm soát

```python
# Option 1: Config-based filtering
class BuiltinConfig:
    include_builtins: bool = True
    include_categories: set[BuiltinCategory] = {
        BuiltinCategory.IO,
        BuiltinCategory.ASYNC,
        BuiltinCategory.HIGHER_ORDER,
    }
    # Mặc định exclude PURE vì ít giá trị, nhiều noise
    exclude_categories: set[BuiltinCategory] = {
        BuiltinCategory.PURE,
    }

# Option 2: Query-time filtering
# Graph lưu TẤT CẢ, query Cypher filter theo category
MATCH (f:Function)-[:CALLS]->(b:BuiltinFunction)
WHERE b.category <> 'pure'
RETURN f.name, b.name
```

## 8. Cân nhắc và Trade-offs

### Nên làm

| Aspect | Recommendation |
|--------|---------------|
| **Include tất cả builtins** | Có, nhưng phân loại category |
| **Deduplicate nodes** | Bắt buộc - chỉ tạo 1 node per unique builtin |
| **Metadata phong phú** | category, side_effect, accepts_callback |
| **Config toggle** | Cho phép user chọn include/exclude |
| **Separate labels** | BuiltinFunction/BuiltinModule thay vì reuse Function |

### Không nên

| Aspect | Lý do |
|--------|-------|
| **Thêm RelationshipType riêng (CALLS_BUILTIN)** | Redundant - node label đã phân biệt |
| **Tạo node cho EVERY prototype method** | Quá nhiều - chỉ tạo khi thực sự được gọi |
| **Deep source analysis trên builtins** | Không có source code, chỉ cần metadata |
| **Lazy load từ DB** | Check DB mỗi call tạo latency, dùng in-memory set |

## 9. Tóm tắt

Giải pháp "System Nodes" là approach tốt hơn skip hoàn toàn vì:

1. **Giữ được call chain đầy đủ** mà không mất thông tin
2. **Phân biệt rõ ràng** user code vs system code qua label riêng (BuiltinFunction vs Function)
3. **Metadata phong phú** cho phép query thông minh (side-effect analysis, purity check)
4. **Performance overhead nhỏ** (~1% nodes, ~10-16% relationships) và có thể kiểm soát qua config
5. **RAG quality tăng đáng kể** - trả lời được nhiều loại câu hỏi hơn

### Thay đổi cần thực hiện

1. Thêm 2 NodeLabel mới: `BUILTIN_MODULE`, `BUILTIN_FUNCTION`
2. Thêm `BuiltinCategory` enum
3. Thêm `BUILTIN_METADATA` dictionary với metadata cho từng builtin
4. Thêm 2 tracking sets trong `CallProcessor.__init__`
5. Sửa `_ingest_function_calls` bỏ 2 guard skip, thêm logic tạo builtin nodes
6. Thêm method `_ensure_builtin_node`

Scope thay đổi vừa phải, backward compatible nếu thêm config toggle.

## 10. So sánh với các ngôn ngữ khác

| Ngôn ngữ | Approach | Lý do |
|----------|----------|-------|
| **Python** | Skip builtins | Builtins không có callbacks phổ biến |
| **Java** | Keep standard library | Java stdlib có inheritance, interfaces |
| **C++** | Keep STL | STL templates cần type analysis |
| **C#** | Skip .NET builtins | Similar to Java nhưng .NET APIs well-defined |
| **Rust** | Skip std builtins | std có docs rõ ràng, ít callbacks |
| **JavaScript** | **Hybrid** | Nhiều builtins với callbacks → System Nodes là best fit |

JavaScript là ngôn ngữ đặc biệt vì:
- Nhiều higher-order functions (`map`, `filter`, `reduce`)
- Phổ biến callbacks và promises
- Console I/O rất phổ biến trong debug và logging
- Async/await patterns với `setTimeout`, `fetch`, `Promise`

Do đó, "System Nodes" approach là **best practice** cho JavaScript.
