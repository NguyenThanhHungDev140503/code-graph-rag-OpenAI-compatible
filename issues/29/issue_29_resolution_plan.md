# Issue #28 Resolution Plan: C# Method Modifier Handlers (async, sealed, virtual, abstract, override)

## Executive Summary

C# method modifiers (`async`, `await`, `sealed`, `virtual`, `abstract`, `override`) are not being properly extracted and indexed in the knowledge graph. Currently, only `async/await` has partial support through `type_inference.py` for resolving async library calls, but the actual modifier extraction from AST nodes is missing.

## Current Problem

### Missing Modifier Extraction

When analyzing C# code with modifiers like:

```csharp
public abstract class Animal
{
    public virtual void Speak() => Console.WriteLine("...");

    public sealed override void Move() => Console.WriteLine("Moving");

    public async Task<int> GetDataAsync()
    {
        await Task.Delay(100);
        return 42;
    }
}
```

The knowledge graph is missing:
1. `virtual` modifier information on `Speak()` method
2. `sealed override` modifier information on `Move()` method
3. `abstract` modifier information on `Animal` class
4. `async` modifier extraction on `GetDataAsync()` method

### Root Causes

#### Root Cause 1: No C# Modifier Constants
**Location**: `codebase_rag/constants.py`
**Issue**: Java has modifier constants (`JAVA_MODIFIER_ABSTRACT`, `JAVA_METHOD_MODIFIERS`, etc.) but C# has only `CSHARP_MODIFIER = "modifier"` without specific modifier value constants.

#### Root Cause 2: No C# Modifier Extraction Function
**Location**: `codebase_rag/parsers/csharp/`
**Issue**: No equivalent to `java/utils.py:extract_from_modifiers_node()` for C#.

#### Root Cause 3: Incomplete Handler Integration
**Location**: `codebase_rag/parsers/handlers/registry.py`
**Issue**: No C#-specific handler registered for modifier extraction.

## Implementation Phases

### Phase 1: Add C# Modifier Constants (P0 - Immediate)
**Duration**: 30 minutes
**Files to modify**: `codebase_rag/constants.py`

Implementation:
```python
# C# Method Modifiers
CSHARP_MODIFIER_PUBLIC = "public"
CSHARP_MODIFIER_PRIVATE = "private"
CSHARP_MODIFIER_PROTECTED = "protected"
CSHARP_MODIFIER_INTERNAL = "internal"
CSHARP_MODIFIER_STATIC = "static"
CSHARP_MODIFIER_VIRTUAL = "virtual"
CSHARP_MODIFIER_SEALED = "sealed"
CSHARP_MODIFIER_ABSTRACT = "abstract"
CSHARP_MODIFIER_OVERRIDE = "override"
CSHARP_MODIFIER_ABSTRACT_METHOD = "abstract"
CSHARP_MODIFIER_VIRTUAL_METHOD = "virtual"
CSHARP_MODIFIER_SEALED_METHOD = "sealed"
CSHARP_MODIFIER_ASYNC = "async"
CSHARP_MODIFIER_READONLY = "readonly"
CSHARP_MODIFIER_CONST = "const"
CSHARP_MODIFIER_VOLATILE = "volatile"
CSHARP_MODIFIER_NEW = "new"
CSHARP_MODIFIER_PARTIAL = "partial"
CSHARP_MODIFIER_REF = "ref"
CSHARP_MODIFIER_OUT = "out"
CSHARP_MODIFIER_IN = "in"
CSHARP_MODIFIER_PARAMS = "params"
CSHARP_MODIFIER_STATIC_READONLY = "readonly"
CSHARP_MODIFIER_THREAD_LOCAL = "thread_local"
CSHARP_MODIFIER_VOLATILE_FIELD = "volatile"

CSHARP_METHOD_MODIFIERS = frozenset({
    CSHARP_MODIFIER_PUBLIC,
    CSHARP_MODIFIER_PRIVATE,
    CSHARP_MODIFIER_PROTECTED,
    CSHARP_MODIFIER_INTERNAL,
    CSHARP_MODIFIER_STATIC,
    CSHARP_MODIFIER_VIRTUAL,
    CSHARP_MODIFIER_SEALED,
    CSHARP_MODIFIER_ABSTRACT,
    CSHARP_MODIFIER_OVERRIDE,
    CSHARP_MODIFIER_ASYNC,
    CSHARP_MODIFIER_NEW,
    CSHARP_MODIFIER_PARTIAL,
})

CSHARP_CLASS_MODIFIERS = frozenset({
    CSHARP_MODIFIER_PUBLIC,
    CSHARP_MODIFIER_PRIVATE,
    CSHARP_MODIFIER_PROTECTED,
    CSHARP_MODIFIER_INTERNAL,
    CSHARP_MODIFIER_STATIC,
    CSHARP_MODIFIER_ABSTRACT,
    CSHARP_MODIFIER_SEALED,
    CSHARP_MODIFIER_PARTIAL,
})

CSHARP_FIELD_MODIFIERS = frozenset({
    CSHARP_MODIFIER_PUBLIC,
    CSHARP_MODIFIER_PRIVATE,
    CSHARP_MODIFIER_PROTECTED,
    CSHARP_MODIFIER_INTERNAL,
    CSHARP_MODIFIER_STATIC,
    CSHARP_MODIFIER_READONLY,
    CSHARP_MODIFIER_CONST,
    CSHARP_MODIFIER_VOLATILE,
    CSHARP_MODIFIER_NEW,
})

CSHARP_PROPERTY_MODIFIERS = frozenset({
    CSHARP_MODIFIER_PUBLIC,
    CSHARP_MODIFIER_PRIVATE,
    CSHARP_MODIFIER_PROTECTED,
    CSHARP_MODIFIER_INTERNAL,
    CSHARP_MODIFIER_STATIC,
    CSHARP_MODIFIER_VIRTUAL,
    CSHARP_MODIFIER_SEALED,
    CSHARP_MODIFIER_ABSTRACT,
    CSHARP_MODIFIER_OVERRIDE,
    CSHARP_MODIFIER_NEW,
    CSHARP_MODIFIER_REQUIRED,
    CSHARP_MODIFIER_INIT,
})
```

### Phase 2: Create C# Modifier Extraction Module (P0 - Immediate)
**Duration**: 2-3 hours
**Files to create**: `codebase_rag/parsers/csharp/modifiers.py`

Implementation:
```python
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ...constants import CSHARP_METHOD_MODIFIERS, CSHARP_CLASS_MODIFIERS
from ..utils import safe_decode_text

if TYPE_CHECKING:
    from tree_sitter import Node

@dataclass
class ModifierInfo:
    modifiers: list[str]
    is_abstract: bool
    is_virtual: bool
    is_sealed: bool
    is_override: bool
    is_async: bool
    is_static: bool
    visibility: str

def extract_csharp_modifiers(
    node: Node,
    allowed_modifiers: frozenset[str]
) -> ModifierInfo:
    """Extract modifiers from C# declaration node.

    Tree-sitter structure for C# modifiers:
    method_declaration
      modifier (public)
      modifier (static)
      modifier (async)
      return_type
      identifier (MethodName)
      parameter_list
    """
    result = ModifierInfo(
        modifiers=[],
        is_abstract=False,
        is_virtual=False,
        is_sealed=False,
        is_override=False,
        is_async=False,
        is_static=False,
        visibility="private"
    )

    modifiers_node = next(
        (child for child in node.children if child.type == "modifier"),
        None
    )

    if not modifiers_node:
        return result

    for modifier_child in modifiers_node.children:
        if modifier_child.type != "modifier":
            continue
        if modifier_text := safe_decode_text(modifier_child):
            result.modifiers.append(modifier_text)

            match modifier_text:
                case "public":
                    result.visibility = "public"
                case "private":
                    result.visibility = "private"
                case "protected":
                    result.visibility = "protected"
                case "internal":
                    result.visibility = "internal"
                case "abstract":
                    result.is_abstract = True
                case "virtual":
                    result.is_virtual = True
                case "sealed":
                    result.is_sealed = True
                case "override":
                    result.is_override = True
                case "async":
                    result.is_async = True
                case "static":
                    result.is_static = True

    return result

def extract_method_modifiers(method_node: Node) -> ModifierInfo:
    """Extract modifiers from C# method declaration."""
    return extract_csharp_modifiers(method_node, CSHARP_METHOD_MODIFIERS)

def extract_class_modifiers(class_node: Node) -> ModifierInfo:
    """Extract modifiers from C# class/interface/struct declaration."""
    return extract_csharp_modifiers(class_node, CSHARP_CLASS_MODIFIERS)
```

### Phase 3: Create C# Language Handler (P1 - Short-term)
**Duration**: 1-2 hours
**Files to create**: `codebase_rag/parsers/handlers/csharp.py`

```python
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseLanguageHandler
from ..csharp import modifiers as csharp_modifiers

if TYPE_CHECKING:
    from ...types_defs import ASTNode

class CSharpHandler(BaseLanguageHandler):
    def extract_modifiers(self, node: ASTNode) -> csharp_modifiers.ModifierInfo:
        return csharp_modifiers.extract_csharp_modifiers(node, csharp_modifiers.CSHARP_METHOD_MODIFIERS)

    def extract_decorators(self, node: ASTNode) -> list[str]:
        return []
```

### Phase 4: Update Registry and Integration (P1 - Short-term)
**Duration**: 1 hour
**Files to modify**:
- `codebase_rag/parsers/handlers/registry.py` - Add CSharpHandler
- `codebase_rag/parsers/definition_processor.py` - Use modifier extraction

### Phase 5: Add Tree-sitter Query for Modifiers (P1 - Short-term)
**Duration**: 1 hour
**Files to modify**: `codebase_rag/language_spec.py`

Update C# LanguageSpec to include modifier_query:
```python
cs.SupportedLanguage.CSHARP: LanguageSpec(
    ...
    modifier_query="""
    (method_declaration
        (modifier) @modifier
        name: (identifier) @name) @method
    (class_declaration
        (modifier) @modifier
        name: (identifier) @name) @class
    """
)
```

### Phase 6: Add Tests (P1 - Short-term)
**Duration**: 2 hours
**Files to modify**: `codebase_rag/tests/`

Test cases:
```python
def test_csharp_async_method_modifier():
    """Test async modifier extraction from method"""

def test_csharp_virtual_sealed_override_modifiers():
    """Test virtual, sealed, override modifiers"""

def test_csharp_abstract_class_modifier():
    """Test abstract modifier on class"""

def test_csharp_modifier_combinations():
    """Test various modifier combinations"""
```

## Test Cases

### Test 1: Async/Await Modifier
```csharp
public async Task<string> FetchDataAsync()
{
    await Task.Delay(100);
    return "data";
}
// Expected: method has is_async=True, creates CALLS to Task.Delay
```

### Test 2: Virtual Method
```csharp
public virtual void DoSomething()
{
    Console.WriteLine("Base implementation");
}
// Expected: method has is_virtual=True
```

### Test 3: Sealed Override
```csharp
public sealed override void Move()
{
    Console.WriteLine("Moving");
}
// Expected: method has is_sealed=True, is_override=True
```

### Test 4: Abstract Class and Method
```csharp
public abstract class Animal
{
    public abstract void Speak();
}
// Expected: class has is_abstract=True, method has is_abstract=True
```

## Success Metrics

| Metric | Before | After |
|--------|--------|-------|
| Modifier extraction for C# | 0 modifiers | All modifiers extracted |
| async method detection | Partial (library calls only) | Full (modifier-based) |
| virtual/sealed/override | Not tracked | Fully tracked |
| abstract class detection | Not tracked | Fully tracked |

## Architecture Integration

```
codebase_rag/
├── constants.py                    # Added C# modifier constants
├── parsers/
│   ├── csharp/
│   │   ├── modifiers.py            # NEW - Modifier extraction
│   │   ├── type_inference.py       # Enhanced for async
│   │   └── __init__.py
│   └── handlers/
│       ├── csharp.py              # NEW - C# handler
│       └── registry.py             # Updated
└── language_spec.py                # Updated with modifier query
```

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tree-sitter modifier node changes | Low | Medium | Test with multiple C# grammars |
| Performance impact on large files | Medium | Low | Cache modifier extraction |
| Breaking existing functionality | Low | High | Run existing tests before/after |

## Timeline Estimate

| Phase | Effort | Priority |
|-------|--------|----------|
| Phase 1: Constants | 30 min | P0 |
| Phase 2: Modifier Module | 2-3 hours | P0 |
| Phase 3: C# Handler | 1-2 hours | P1 |
| Phase 4: Registry Integration | 1 hour | P1 |
| Phase 5: Tree-sitter Query | 1 hour | P1 |
| Phase 6: Tests | 2 hours | P1 |

**Total**: 8-10 hours

## Related Issues

- Issue #17: CALLS Relationships Missing
- Issue #23: C# Records Not Being Indexed
- Issue #26: LINQ Query Analyzer

## Decision Required

- [ ] Approve implementation approach
- [ ] Prioritize against other issues
- [ ] Consider async modifier handling in call resolution
