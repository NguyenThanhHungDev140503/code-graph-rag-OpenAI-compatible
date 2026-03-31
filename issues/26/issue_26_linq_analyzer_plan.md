# Issue #26: Implement LINQ Query Analyzer for CALLS Relationships

## Status: OPEN

## Summary

LINQ query expressions (C# query syntax) are parsed by tree-sitter but do not create CALLS relationships in the knowledge graph. This means LINQ queries like:

```csharp
var result = from n in numswhere n > 1
             select n * 2;
```

Are not analyzed for their method call equivalents:

```csharp
var result = nums.Where(n => n > 1).Select(n => n * 2);
```

## ProblemAnalysis

### Current Tree-sitter Parsing

When parsing LINQ query_expression, tree-sitter produces:

```
query_expression: "from n in nums..."
  from_clause: "from n in nums"
    from: "from"
    identifier: "n"← lambda parameter
    in: "in"
    identifier: "nums"  ← source (not a call)
  where_clause: "where n > 1"
    where: "where"
    binary_expression: "n > 1"  ← expression (not a call)
  select_clause: "select n * 2"
    select: "select"
    binary_expression: "n * 2"  ← expression (not a call)
```

### Why No CALLS Relationships

1. **No invocation_expression nodes**: LINQ clauses don't contain direct method calls
2. **Query syntax transformation is semantic**: `where x > 5` → `Where(x => x > 5)` requires type inference
3. **Extension method resolution needed**: Must know the source type to resolve System.Linq extensions

## Implementation Plan

### Phase 0: C# Handler Creation (Prerequisite)

**Goal**: Create C# language handler and register it in the handler registry

**Problem**: C# currently falls back to `BaseLanguageHandler` because no dedicated handler exists. The `linq_analyzer.py` needs a handler to integrate properly.

**Implementation**:
```python
codebase_rag/parsers/handlers/csharp.py  # NEW - CSharpHandler class
codebase_rag/parsers/handlers/registry.py  # MODIFY - register CSHARP
```

**Key Tasks**:
- Create `CSharpHandler` class extending `BaseLanguageHandler`
- Register `SupportedLanguage.CSHARP` → `CSharpHandler` in `registry.py`
- Implement `process_query_expression()` hook in handler

**Files to Create/Modify**:
| File | Action |
|------|--------|
| `codebase_rag/parsers/handlers/csharp.py` | CREATE |
| `codebase_rag/parsers/handlers/registry.py` | MODIFY |
| `codebase_rag/parsers/csharp/__init__.py` | MODIFY (add exports) |

### Phase 1: Basic Pattern Recognition

**Goal**: Parse query_expression and identify clause types

**Implementation**:
```python
codebase_rag/parsers/csharp/linq_analyzer.py
```

**Key Functions**:
- `parse_query_expression(node)` → Extract clause structure
- `identify_clause_type(clause)` → Map clause to LINQ method
- `extract_source(query)` → Get thedata source

**Clause → Method Mapping**:
| Clause | Method |
|--------|--------|
| from_clause | SelectMany (multiple) / source |
| where_clause | Where |
| select_clause | Select |
| orderby_clause | OrderBy/OrderByDescending |
| group_clause | GroupBy |
| join_clause | Join |
| let_clause | Select (with anonymous type) |

### Phase 2: Extension Method Resolution

**Goal**: Resolve System.Linq extension methods

**Implementation**:
- Extend existing `CSharpTypeInferenceEngine.resolve_linq_expression()` in `type_inference.py`
- Leverage existing `linq` methods registry (`known_library_methods["linq"]`)
- Add System.Linq extension method registry for new operators
- Handle IEnumerable<T> vs IQueryable<T>

**Existing Code to Leverage**:
- `type_inference.py:400-433` - `resolve_linq_expression()` already handles keyword → method resolution
- `constants.py:1483-1630` - `CSHARP_STDLIB_METHODS` already defines LINQ method metadata

**Key Methods**:
- `Where(predicate)`
- `Select(selector)`
- `OrderBy(keySelector)` / `OrderByDescending`
- `ThenBy(keySelector)`
- `GroupBy(keySelector)`
- `Join(inner, outerKey, innerKey, resultSelector)`
- `SelectMany(selector)`

### Phase 3: Lambda Parameter Tracking

**Goal**: Track lambda parameters across clauses for accurate expression analysis

**Example**:
```csharp
from n in nums
where n > 1
select n * 2
```

Lambda scope:
- `n` is introduced in from_clause
- `n` is used in where_clause predicate
- `n` is used in select_clause projection

### Phase 4: CALLS Relationship Creation

**Goal**: Create CALLS relationships for resolved methods

**Implementation**:
- Modify `call_processor.py:_ingest_function_calls()` to recognize `query_expression` nodes
- Add `query_expression` to C# node types in line ~590
- Create CALLS edges from containing function to resolved LINQ methods
- Handle method chaining (fluent API)

**Code Changes Required**:
```python
# call_processor.py ~line 590
is_csharp_invocation = (
    language == cs.SupportedLanguage.CSHARP
    and call_node.type in (
        "invocation_expression",
        "query_expression",           # NEW - LINQ support
        "object_creation_expression",
        ...
    )
)
```

## Architecture Integration

```
codebase_rag/
├── parsers/
│   ├── csharp/
│   │   ├── linq_analyzer.py      # NEW - LINQ query expression parser
│   │   ├── type_inference.py     # ENHANCED - extend resolve_linq_expression()
│   │   └── __init__.py           # MODIFY - export linq_analyzer
│   ├── handlers/
│   │   ├── csharp.py             # NEW - CSharpHandler (Phase 0)
│   │   ├── registry.py           # MODIFY - register CSHARP handler
│   │   ├── base.py               # Reference
│   │   └── java.py               # Reference for handler structure
│   └── call_processor.py         # MODIFY - add query_expression handling
└── constants.py                   # CSHARP_QUERY_EXPRESSION (already exists)
```

**Integration Flow**:
```
Tree-sitter parses C# file
        ↓
BaseLanguageHandler routes to CSharpHandler
        ↓
CSharpHandler detects query_expression node
        ↓
linq_analyzer.py parses clause structure
        ↓
type_inference.py resolves LINQ methods
        ↓
call_processor.py creates CALLS relationships
```

## Test Cases

### Test 1: Basic Query
```csharp
var result = from n in numbers
             where n > 0
             select n * 2;
// Expected CALLS: numbers.Where, Where().Select
```

### Test 2: Multiple from Clauses
```csharp
var result = from x in xs
             from y in ys
             select new { x, y };
// Expected CALLS: xs.SelectMany
```

### Test 3: JoinClause
```csharp
var result = from c in customers
             join o in orders on c.Id equals o.CustomerId
             select new { c.Name, o.OrderDate };
// Expected CALLS: customers.Join
```

### Test 4: GroupBy
```csharp
var result = from p in products
             group p by p.Category into g
             select new { Category = g.Key, Count = g.Count() };
// Expected CALLS: products.GroupBy, GroupBy().Count
```

### Test 5: Nested LINQ Queries
```csharp
var result = from c in categories
             select new {
                 Category = c.Name,
                 ExpensiveProducts = from p in products
                                     where p.CategoryId == c.Id && p.Price > 100
                                     select p.Name
             };
// Expected CALLS: categories.Select, products.Where (nested)
```

### Test 6: Query Expression in Method Chain
```csharp
var result = GetData()
    .Where(x => x.IsActive)
    .Select(x => x.Value)
    .Where(v => v > 0)
    .ToList();
// Expected CALLS: GetData, Where, Select, Where, ToList
```

## Benefits

1. **Complete CALLS coverage** for LINQ-based code
2. **Data flow understanding** through lambda analysis
3. **Accurate dependency analysis** for functional-style C#
4. **Better refactoring support** for query transformations

## Risks and Considerations

### Risk 1: Type Inference Complexity
- **Mitigation**: Start with common patterns, fail gracefully for complex cases

### Risk 2: Extension Method Ambiguity
- **Mitigation**: Use System.Linq methods as defaults, allow configuration

### Risk 3: Performance Impact
- **Mitigation**: Lazy evaluation, cache resolved types

## Related Files

### Existing Files (to Modify)
| File | Changes |
|------|---------|
| `codebase_rag/constants.py` | CSHARP_QUERY_EXPRESSION (already defined) |
| `codebase_rag/parsers/csharp/type_inference.py` | Extend `resolve_linq_expression()` |
| `codebase_rag/parsers/csharp/__init__.py` | Add linq_analyzer exports |
| `codebase_rag/parsers/handlers/registry.py` | Register CSharpHandler |
| `codebase_rag/call_processor.py` | Add `query_expression` node handling |

### New Files (to Create)
| File | Purpose |
|------|---------|
| `codebase_rag/parsers/handlers/csharp.py` | CSharpHandler class |
| `codebase_rag/parsers/csharp/linq_analyzer.py` | LINQ query expression parser |

## Timeline Estimate

| Phase | Effort | Priority | Notes |
|------|--------|----------|-------|
| Phase 0: C# Handler Creation | 1 day | High | Prerequisite - enables integration |
| Phase 1: Pattern Recognition | 2-3 days | Medium | Core LINQ clause parsing |
| Phase 2: Method Resolution | 1-2 days | Medium | Leverage existing resolve_linq_expression() |
| Phase 3: Lambda Tracking | 2-3 days | Low | Can be deferred post-MVP |
| Phase 4: CALLS Integration | 1-2 days | Medium | call_processor modification |

**Total**: 7-11 days (excludes deferred Phase 3)

## Decision Required

- [ ] Approve implementation approach
- [ ] Prioritize against other issues
- [ ] Decide on Phase 3 value (lambda tracking may be low ROI)
- [x] **Added Phase 0** - C# Handler creation is prerequisite (1 day effort)
- [x] **Updated Phase 2** - Leverage existing `resolve_linq_expression()` method

## Related Issues

- #20 - Dynamic C# call type discovery
- #25 - C# Embedding Query Incomplete

## Existing Code to Leverage

The following code already exists and should be extended rather than rewritten:

### LINQ Method Resolution
```python
# type_inference.py:400-433
def resolve_linq_expression(self, call_name: str) -> str | None:
    """Converts LINQ keyword to fully qualified method name."""
    linq_keywords = {
        "where", "select", "any", "all", "first", "firstordefault",
        "count", "sum", "min", "max", "average", "aggregate",
        "orderby", "orderbydescending", "thenby", "thenbydescending",
        "groupby", "take", "skip", "distinct", "union", "tolist", "toarray",
    }
    if call_name.lower() in linq_keywords:
        return f"csharp.stdlib.Linq.{call_name.title()}"
    return None
```

### Known LINQ Methods Registry
```python
# type_inference.py:12-352 - _init_known_library_methods()
known_library_methods = {
    "linq": {
        "Select", "Where", "First", "FirstOrDefault", "Any", "All",
        "Count", "LongCount", "Sum", "Min", "Max", "Average", "Aggregate",
        "OrderBy", "OrderByDescending", "ThenBy", "ThenByDescending",
        "GroupBy", "Join", "GroupJoin", "Take", "Skip", "TakeWhile", "SkipWhile",
        "Distinct", "Union", "Intersect", "Except", "ToList", "ToArray",
        "ToDictionary", "ToLookup", "OfType", "Cast", "AsEnumerable",
        # ... more
    }
}
```

### Constants for LINQ Methods
```python
# constants.py:1483-1630
CSHARP_STDLIB_METHODS = {
    "Enumerable.Select": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    "Enumerable.Where": {"category": "higher_order", "module": "Enumerable", "accepts_callback": True},
    # ... already defines metadata for LINQ methods
}
```
