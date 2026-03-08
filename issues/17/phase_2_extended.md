# Issue #17 Resolution Plan - Phase 2 Mở Rộng

## Tóm Tắt Vấn Đề

Sau khi hoàn thành Phase 1 và Phase 2 cơ bản, graph vẫn còn **3,618 UnresolvedFunction nodes**:

| Category | Count | Percentage |
|----------|-------|------------|
| Property getter/setter | 619 | 17.1% |
| Array.map() | 334 | 9.2% |
| Array.filter() | 53 | 1.5% |
| C# extension methods | ~1000+ | ~30% |
| Promise/async | ~200+ | ~5% |

---

## Phase 2 Mở Rộng: Cải Thiện Resolution

### Mục Tiêu
Giảm số UnresolvedFunction nodes từ 3,618 xuống <1,000 (resolution rate 70%+)

---

## Tasks Chi Tiết

### Task 1: Thêm JS/TS Stdlib Methods

**Files cần sửa:** `codebase_rag/parsers/call_resolver.py`

**Thêm vào JS/TS stdlib methods:**

```python
# Array methods
JAVASCRIPT_STDLIB_METHODS = {
    "map", "filter", "reduce", "forEach", "find", "findIndex",
    "some", "every", "sort", "slice", "splice", "push", "pop",
    "shift", "unshift", "concat", "join", "split", "reverse",
    "includes", "indexOf", "flat", "flatMap", "toFixed", "toString"
}

# Promise methods
PROMISE_METHODS = {
    "then", "catch", "finally", "resolve", "reject", "all", "race"
}

# React hooks (React)
REACT_HOOKS = {
    "useState", "useEffect", "useContext", "useReducer", "useRef",
    "useMemo", "useCallback", "useLayoutEffect", "useDebugValue"
}

# Object methods
OBJECT_METHODS = {
    "hasOwnProperty", "toString", "valueOf", "keys", "values", "entries"
}
```

### Task 2: Thêm C# Extension Methods

**File:** `codebase_rag/parsers/csharp/type_inference.py`

**Thêm vào known_library_methods:**

```python
# More FluentValidation
"FluentValidation": {
    "WithMessage", "NotEmpty", "NotNull", "NotEqual", "Equal",
    "LessThan", "GreaterThan", "Length", "Email", "CreditCard",
    "RuleFor", "ForMember", "Cascade", "When", "Unless",
    "Validate", "ValidateAsync"
}

# More Entity Framework Core
"EntityFramework": {
    "HasKey", "HasMaxLength", "HasColumnName", "IsRequired",
    "HasForeignKey", "HasMany", "HasOne", "WithOne", "WithMany",
    "Include", "ThenInclude", "AsNoTracking", "AsTracking",
    "SaveChangesAsync", "AddAsync", "UpdateAsync", "RemoveAsync"
}

# More MediatR
"MediatR": {
    "SendAsync", "PublishAsync", "CreateStream", "CreatePipe"
}

# ASP.NET Core
"AspNetCore": {
    "MapGet", "MapPost", "MapPut", "MapDelete", "MapControllers",
    "AddScoped", "AddSingleton", "AddTransient",
    "UseEndpoints", "UseRouting", "UseAuthorization"
}
```

### Task 3: Handle Generic Types

**File:** `codebase_rag/parsers/csharp/type_inference.py`

```python
def resolve_generic_method(self, call_name: str) -> str | None:
    # Handle: AddExceptionHandler<CustomExceptionHandler>
    # Extract: AddExceptionHandler
    import re
    generic_match = re.match(r"(\w+)<", call_name)
    if generic_match:
        method_name = generic_match.group(1)
        if method_name in self.all_known_methods:
            return f"csharp.stdlib.{self.get_library_method_type(method_name)}.{method_name}"
    return None
```

### Task 4: Handle Property Access Patterns

**File:** `codebase_rag/parsers/call_resolver.py`

```python
# JS/TS property access
if language == JAVASCRIPT:
    # Check if it's a property (not a function call)
    if self._is_property_access(call_name, caller_node):
        return (NodeLabel.STDLIB_PROPERTY, f"js.stdlib.property.{call_name}")
```

---

## Thứ Tự Thực Hiện

| Task | Priority | Ước Tính |
|------|----------|-----------|
| Task 1: JS/TS Array methods | P0 | 1-2 hours |
| Task 2: C# Extension methods | P0 | 2-3 hours |
| Task 3: Handle Generic Types | P1 | 1-2 hours |
| Task 4: Property Access | P1 | 1-2 hours |

---

## Expected Results

| Metric | Before | After (Expected) |
|--------|--------|-----------------|
| UnresolvedFunction | 3,618 | <1,000 |
| Resolution Rate | 92.8% | 95%+ |
| Total StdlibMethod | 73 | 500+ |

---

## Files Cần Thay Đổi

1. `codebase_rag/parsers/call_resolver.py` - Add JS/TS methods
2. `codebase_rag/parsers/csharp/type_inference.py` - Add C# methods + generics

---

## Status

- Phase 1: ✅ Complete
- Phase 2 (basic): ✅ Complete
- Phase 2 (extended): 🔄 Ready to Start

---

**Last Updated:** 2026-03-08 17:15 UTC
