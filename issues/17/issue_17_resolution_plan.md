# Issue #17 Resolution Plan: CALLS Relationships Missing - Complete Plan

## Executive Summary

This document outlines a comprehensive plan to resolve Issue #17, which reports severely missing CALLS relationships in the graph database, particularly internal Function to Function calls.

## Current Problem

The graph database is missing approximately 95% of CALLS relationships. Tree-sitter detects around 4,782 function calls, but only 181 are saved to the graph (3.8% capture rate). The main issue is that unresolved calls are completely skipped and not stored.

## Root Causes

The investigation has identified five root causes. First, unresolved calls are skipped in the code at call_processor.py lines 726-727 where an else continue statement causes unresolved calls to be discarded entirely. Second, C# call queries are limited because only member_expression is detected while invocation_expression, object_creation_expression, and element_access_expression are missing. Third, the resolution logic lacks type inference for C# because C# uses namespace-based qualified names like System.IO.File that do not match the file-path based QN in function_registry. Fourth, C# method resolution is incomplete as resolve_method_calls only handles stdlib calls and does not handle instance method calls. Fifth, CSharpTypeInferenceEngine is missing because Java type inference is being reused for C# as a temporary workaround, but C# has unique syntax patterns that are not supported.

## Resolution Phases

### Phase 1: Store Unresolved Calls (P0 - Immediate)

The first phase focuses on quick wins to capture 95% or more of calls immediately within 2 to 4 hours. The implementation requires modifying call_processor.py to store unresolved calls instead of skipping them. The code change involves replacing the else continue pattern with code that creates UNRESOLVED_FUNCTION nodes with qualified names in the format unresolved.moduleQN.callName. This approach ensures that all detected calls are captured in the graph, even if their targets cannot be fully resolved.

### Phase 2: CSharpTypeInferenceEngine (P1 - Short-term)

The second phase aims to achieve 80% or more resolution rate for C# within 3 to 5 days. This phase involves creating a new C# Type Inference Engine at parsers/csharp/type_inference.py with a CSharpTypeInferenceEngine class. The new engine needs to handle LINQ expressions like list.Where(x => x > 5), property access like obj.Property with get and set, indexers like this[int i], async and await patterns like await Task.Run(), and constructor calls like new Class(). After creating the engine, it must be integrated into CallResolver by modifying type_inference.py to route C# to the new engine, and updating resolve_csharp_method_call to use the new engine. Finally, test cases for C# specific patterns should be created to benchmark resolution rate improvements.

### Phase 3: Re-resolve and Clean Graph (P2 - Medium-term)

The third phase targets cleaning the graph with high confidence relationships within 1 to 2 days. Two implementation options exist. The first option involves re-running resolution on stored unresolved calls and updating relationships with resolved targets. The second option implements query-time resolution that attempts to resolve unresolved relationships during queries and returns both resolved and unresolved results.

## Implementation Priority

The priority order starts with Store Unresolved as P0 requiring 2 to 4 hours with no dependencies. Next is CSharpTypeInferenceEngine as P1 requiring 3 to 5 days and depending on P0. Finally, Re-resolve or Query-time Resolution as P2 requires 1 to 2 days and depends on both P0 and P1.

## Success Metrics

The plan defines specific targets for each phase. Capture rate should improve from the current 3.8% to 95% or more. Resolution rate should improve from the current 31% to 80 C# resolution should% or more. improve from approximately 0% to 80% or more. Total CALLS in the graph should increase from the current 161 to approximately 4,500.

## Risks and Mitigations

Several risks have been identified with probability, impact, and mitigation strategies. C# namespace resolution not matching has high probability and high impact, and the mitigation is to add fuzzy namespace to file path mapping. Too many edge cases has medium probability and medium impact, and the mitigation is to prioritize common patterns first. Graph becoming too large has medium probability and low impact, and the mitigation is to add a cleanup script for old unresolved entries. Performance degradation has low probability and medium impact, and the mitigation is to benchmark after each change.

## Related Issues

Issue #13 covers C# Methods Not Created, which is related to this issue.

## Conclusion

The hybrid approach is recommended because it provides immediate data capture through Store Unresolved while working on proper resolution through CSharpTypeInferenceEngine. This ensures no data is lost and enables graph cleanup after the C# engine is complete.
