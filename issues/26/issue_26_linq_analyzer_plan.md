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
3. **Extension method resolution needed**: Must know the source type to resolve System.Linq extensions## Implementation Plan

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
- Integrate with `type_inference.py`
- Add System.Linq extension method registry
- Handle IEnumerable<T> vs IQueryable<T>

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
- Integrate with `call_processor.py`
- Create CALLS edges from containing function to resolved LINQ methods
- Handle method chaining (fluent API)

## Architecture Integration

```
codebase_rag/
├── parsers/
│   └── csharp/
│       ├── linq_analyzer.py      # NEW
│       ├── type_inference.py     # Enhanced for LINQ
│       └── handler.py            # Integration point
└── call_processor.py             # Receive LINQ calls
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

- `codebase_rag/constants.py` - CSHARP_QUERY_EXPRESSION (already defined)
- `codebase_rag/parsers/csharp/type_inference.py` - Type resolution
- `codebase_rag/call_processor.py` - CALLS relationship creation

## Timeline Estimate

| Phase | Effort | Priority |
|------|--------|----------|
|Phase 1: Pattern Recognition | 2-3 days | Medium |
| Phase 2: Method Resolution | 3-5 days | Medium |
| Phase 3: Lambda Tracking | 2-3 days | Low |
| Phase 4: CALLS Integration | 1-2 days | Medium |

**Total**: 8-13 days

## Decision Required

- [ ] Approve implementation approach
- [ ] Prioritize against other issues
- [ ] Decide on Phase 3 value (lambda tracking may be low ROI)

## Related Issues

- #20 - Dynamic C# call type discovery
- #25 - C# Embedding Query Incomplete
