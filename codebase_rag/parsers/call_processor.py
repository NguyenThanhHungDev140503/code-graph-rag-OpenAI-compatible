from __future__ import annotations

from pathlib import Path

from loguru import logger
from tree_sitter import Node, QueryCursor

from .. import constants as cs
from .. import logs as ls
from ..language_spec import LanguageSpec
from ..services import IngestorProtocol
from ..types_defs import FunctionRegistryTrieProtocol, LanguageQueries
from .call_resolver import CallResolver
from .cpp import utils as cpp_utils
from .import_processor import ImportProcessor
from .type_inference import TypeInferenceEngine
from .utils import get_function_captures, is_method_node


class CallProcessor:
    def __init__(
        self,
        ingestor: IngestorProtocol,
        repo_path: Path,
        project_name: str,
        function_registry: FunctionRegistryTrieProtocol,
        import_processor: ImportProcessor,
        type_inference: TypeInferenceEngine,
        class_inheritance: dict[str, list[str]],
        module_qn_to_file_path: dict[str, Path] | None = None,
    ) -> None:
        self.ingestor = ingestor
        self.repo_path = repo_path
        self.project_name = project_name
        self._file_path_to_module_qn: dict[Path, str] = (
            {v: k for k, v in module_qn_to_file_path.items()}
            if module_qn_to_file_path
            else {}
        )
        self._function_registry = function_registry

        self._resolver = CallResolver(
            function_registry=function_registry,
            import_processor=import_processor,
            type_inference=type_inference,
            class_inheritance=class_inheritance,
        )

        # Track created stdlib nodes to avoid duplicates
        self._created_stdlib_nodes: set[str] = set()
        self._created_stdlib_classes: set[str] = set()

    def _ensure_stdlib_node(
        self,
        stdlib_qn: str,
        call_name: str,
        language: cs.SupportedLanguage,
    ) -> None:
        """Ensure a stdlib method node exists in the graph for Java/C#."""
        if stdlib_qn in self._created_stdlib_nodes:
            return

        # Get metadata from constants
        if language == cs.SupportedLanguage.JAVA:
            metadata = cs.JAVA_STDLIB_METHODS.get(call_name, {})
        elif language == cs.SupportedLanguage.CSHARP:
            metadata = cs.CSHARP_STDLIB_METHODS.get(call_name, {})
        else:
            return

        # Determine class name from call_name (e.g., "System.out.println" -> "System")
        class_name = call_name.split(".")[0]
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
                "has_side_effect": metadata.get("has_side_effect"),
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

    def _get_node_name(self, node: Node, field: str = cs.FIELD_NAME) -> str | None:
        name_node = node.child_by_field_name(field)
        if not name_node:
            return None
        text = name_node.text
        return None if text is None else text.decode(cs.ENCODING_UTF8)

    def process_calls_in_file(
        self,
        file_path: Path,
        root_node: Node,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        relative_path = file_path.relative_to(self.repo_path)
        logger.debug(ls.CALL_PROCESSING_FILE.format(path=relative_path))

        try:
            # (H) Reuse the module QN from definition pass if available,
            # (H) ensuring consistency (e.g. C# namespace-based QN vs file-path QN)
            if file_path in self._file_path_to_module_qn:
                module_qn = self._file_path_to_module_qn[file_path]
            else:
                module_qn = cs.SEPARATOR_DOT.join(
                    [self.project_name] + list(relative_path.with_suffix("").parts)
                )
                if file_path.name in (cs.INIT_PY, cs.MOD_RS):
                    module_qn = cs.SEPARATOR_DOT.join(
                        [self.project_name] + list(relative_path.parent.parts)
                    )

            self._process_calls_in_functions(root_node, module_qn, language, queries)
            self._process_calls_in_classes(root_node, module_qn, language, queries)
            self._process_module_level_calls(root_node, module_qn, language, queries)

        except Exception as e:
            logger.error(ls.CALL_PROCESSING_FAILED.format(path=file_path, error=e))

    def _process_calls_in_functions(
        self,
        root_node: Node,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        result = get_function_captures(root_node, language, queries)
        if not result:
            return

        lang_config, captures = result
        func_nodes = captures.get(cs.CAPTURE_FUNCTION, [])
        for func_node in func_nodes:
            if not isinstance(func_node, Node):
                continue
            if self._is_method(func_node, lang_config):
                continue

            if language == cs.SupportedLanguage.CPP:
                func_name = cpp_utils.extract_function_name(func_node)
            else:
                func_name = self._get_node_name(func_node)
            if not func_name:
                continue
            if func_qn := self._build_nested_qualified_name(
                func_node, module_qn, func_name, lang_config
            ):
                self._ingest_function_calls(
                    func_node,
                    func_qn,
                    cs.NodeLabel.FUNCTION,
                    module_qn,
                    language,
                    queries,
                )

    def _get_rust_impl_class_name(self, class_node: Node) -> str | None:
        class_name = self._get_node_name(class_node, cs.FIELD_TYPE)
        if class_name:
            return class_name
        return next(
            (
                child.text.decode(cs.ENCODING_UTF8)
                for child in class_node.children
                if child.type == cs.TS_TYPE_IDENTIFIER and child.is_named and child.text
            ),
            None,
        )

    def _get_class_name_for_node(
        self, class_node: Node, language: cs.SupportedLanguage
    ) -> str | None:
        if language == cs.SupportedLanguage.RUST and class_node.type == cs.TS_IMPL_ITEM:
            return self._get_rust_impl_class_name(class_node)
        return self._get_node_name(class_node)

    def _process_methods_in_class(
        self,
        body_node: Node,
        class_qn: str,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        method_query = queries[language][cs.QUERY_FUNCTIONS]
        if not method_query:
            return
        method_cursor = QueryCursor(method_query)
        method_captures = method_cursor.captures(body_node)
        method_nodes = method_captures.get(cs.CAPTURE_FUNCTION, [])
        for method_node in method_nodes:
            if not isinstance(method_node, Node):
                continue
            method_name = self._get_node_name(method_node)
            if not method_name:
                continue
            method_qn = f"{class_qn}{cs.SEPARATOR_DOT}{method_name}"
            self._ingest_function_calls(
                method_node,
                method_qn,
                cs.NodeLabel.METHOD,
                module_qn,
                language,
                queries,
                class_qn,
            )

    def _process_calls_in_classes(
        self,
        root_node: Node,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        query = queries[language][cs.QUERY_CLASSES]
        if not query:
            return
        cursor = QueryCursor(query)
        captures = cursor.captures(root_node)
        class_nodes = captures.get(cs.CAPTURE_CLASS, [])

        for class_node in class_nodes:
            if not isinstance(class_node, Node):
                continue
            class_name = self._get_class_name_for_node(class_node, language)
            if not class_name:
                continue
            class_qn = self._resolve_class_qn(class_name, module_qn)
            if body_node := class_node.child_by_field_name(cs.FIELD_BODY):
                self._process_methods_in_class(
                    body_node, class_qn, module_qn, language, queries
                )

    def _resolve_class_qn(self, class_name: str, module_qn: str) -> str:
        """Resolve class QN by looking up the function registry first.

        The definition pass may register class nodes with a different QN
        than what file-path-based module_qn + class_name would produce
        (e.g. C# uses namespace-based QN via resolve_fqn_from_ast).
        """
        # (H) Try the default file-path-based QN first
        default_qn = f"{module_qn}{cs.SEPARATOR_DOT}{class_name}"
        if default_qn in self._function_registry:
            return default_qn

        # (H) Lookup in registry by class name suffix
        # (H) to find the namespace-based QN from definition pass
        if matches := self._function_registry.find_ending_with(class_name):
            # (H) Filter out constructor QNs that end with ClassName.ClassName
            # (H) to avoid returning a method QN instead of the class QN
            ctor_suffix = (
                f"{cs.SEPARATOR_DOT}{class_name}{cs.SEPARATOR_DOT}{class_name}"
            )
            filtered = [m for m in matches if not m.endswith(ctor_suffix)]
            matches = filtered or matches

            if len(matches) == 1:
                return matches[0]
            # (H) Multiple matches: pick the best one by import distance
            best_qn = min(
                matches,
                key=lambda m: self._resolver._calculate_import_distance(module_qn, m),
            )
            return best_qn

        return default_qn

    def _process_module_level_calls(
        self,
        root_node: Node,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        self._ingest_function_calls(
            root_node, module_qn, cs.NodeLabel.MODULE, module_qn, language, queries
        )

    def _get_call_target_name(self, call_node: Node) -> str | None:
        # C#: Handle invocation_expression (used by tree-sitter-c-sharp)
        if call_node.type == "invocation_expression":
            # Get the 'function' field which contains the method being called
            func_node = call_node.child_by_field_name("function")
            if func_node:
                # If it's a member_access_expression (e.g., Console.WriteLine)
                if func_node.type == "member_access_expression":
                    # Get the full text of member_access_expression
                    if func_node.text:
                        return str(func_node.text.decode(cs.ENCODING_UTF8))
                # If it's just an identifier (e.g., Method())
                elif func_node.type == "identifier":
                    if func_node.text:
                        return str(func_node.text.decode(cs.ENCODING_UTF8))

        if func_child := call_node.child_by_field_name(cs.TS_FIELD_FUNCTION):
            match func_child.type:
                case (
                    cs.TS_IDENTIFIER
                    | cs.TS_ATTRIBUTE
                    | cs.TS_MEMBER_EXPRESSION
                    | cs.CppNodeType.QUALIFIED_IDENTIFIER
                    | cs.TS_SCOPED_IDENTIFIER
                ):
                    if func_child.text is not None:
                        return str(func_child.text.decode(cs.ENCODING_UTF8))
                case cs.TS_CPP_FIELD_EXPRESSION:
                    field_node = func_child.child_by_field_name(cs.FIELD_FIELD)
                    if field_node and field_node.text:
                        return str(field_node.text.decode(cs.ENCODING_UTF8))
                case cs.TS_PARENTHESIZED_EXPRESSION:
                    return self._get_iife_target_name(func_child)

        match call_node.type:
            case (
                cs.TS_CPP_BINARY_EXPRESSION
                | cs.TS_CPP_UNARY_EXPRESSION
                | cs.TS_CPP_UPDATE_EXPRESSION
            ):
                operator_node = call_node.child_by_field_name(cs.FIELD_OPERATOR)
                if operator_node and operator_node.text:
                    operator_text = operator_node.text.decode(cs.ENCODING_UTF8)
                    return cpp_utils.convert_operator_symbol_to_name(operator_text)
            case cs.TS_METHOD_INVOCATION:
                object_node = call_node.child_by_field_name(cs.FIELD_OBJECT)
                name_node = call_node.child_by_field_name(cs.FIELD_NAME)
                if name_node and name_node.text:
                    method_name = str(name_node.text.decode(cs.ENCODING_UTF8))
                    if not object_node or not object_node.text:
                        return method_name
                    object_text = str(object_node.text.decode(cs.ENCODING_UTF8))
                    return f"{object_text}{cs.SEPARATOR_DOT}{method_name}"

        if name_node := call_node.child_by_field_name(cs.FIELD_NAME):
            if name_node.text is not None:
                return str(name_node.text.decode(cs.ENCODING_UTF8))

        return None

    def _get_iife_target_name(self, parenthesized_expr: Node) -> str | None:
        for child in parenthesized_expr.children:
            match child.type:
                case cs.TS_FUNCTION_EXPRESSION:
                    return f"{cs.IIFE_FUNC_PREFIX}{child.start_point[0]}_{child.start_point[1]}"
                case cs.TS_ARROW_FUNCTION:
                    return f"{cs.IIFE_ARROW_PREFIX}{child.start_point[0]}_{child.start_point[1]}"
        return None

    def _find_stdlib_key(
        self,
        full_call_name: str | None,
        call_name: str | None,
        stdlib_methods: dict,
    ) -> str | None:
        """Find matching stdlib key from call names.

        Tries multiple formats:
        - full_call_name as-is (e.g., "System.out.println")
        - full_call_name capitalized (e.g., "stream.map" -> "Stream.map")
        - call_name as-is (e.g., "println")
        - call_name capitalized (e.g., "println" -> "Println")
        - Also tries substring matching for stdlib patterns
        """
        candidates = []
        if full_call_name:
            candidates.append(full_call_name)
            # Try capitalized first letter for the object part
            # e.g., "stream.map" -> "Stream.map"
            if "." in full_call_name:
                obj, method = full_call_name.rsplit(".", 1)
                candidates.append(f"{obj.capitalize()}.{method}")
        if call_name and call_name != full_call_name:
            candidates.append(call_name)
            # Try capitalized
            candidates.append(call_name.capitalize())

        # Try exact matches first
        for candidate in candidates:
            if candidate in stdlib_methods:
                return candidate

        # Try substring matching - e.g., "stream.map" matches "Stream.map"
        if full_call_name:
            for stdlib_key in stdlib_methods.keys():
                # Check if stdlib_key is a suffix of full_call_name (case-insensitive)
                if full_call_name.lower().endswith(stdlib_key.lower()):
                    return stdlib_key

        return None

    def _find_stdlib_key_from_qn(
        self,
        callee_qn: str,
        language: cs.SupportedLanguage,
    ) -> str | None:
        """Find stdlib key from resolved qualified name.

        For Java: callee_qn like "java.util.stream.Stream.map" -> "Stream.map"
        For C#: callee_qn like "System.Console.WriteLine" -> "Console.WriteLine"
        """
        stdlib_methods = (
            cs.JAVA_STDLIB_METHODS
            if language == cs.SupportedLanguage.JAVA
            else cs.CSHARP_STDLIB_METHODS
        )

        if not callee_qn:
            return None

        # For Java, extract the class.method part from full qualified name
        # e.g., "java.util.stream.Stream.map" -> "Stream.map"
        if language == cs.SupportedLanguage.JAVA:
            # Try to extract class.method from qualified name
            # Pattern: package.Class.method or package.Class$InnerClass.method
            parts = callee_qn.rsplit(".", 2)
            if len(parts) >= 2:
                class_name = parts[-2]
                method_name = parts[-1]
                candidate = f"{class_name}.{method_name}"
                if candidate in stdlib_methods:
                    return candidate

        # Also try the full callee_qn as-is (for cases like System.out.println)
        if callee_qn in stdlib_methods:
            return callee_qn

        return None

    def _extract_csharp_call_name(self, call_node: Node) -> str | None:
        """Extract full call name from C# invocation_expression.

        For C#, method calls are wrapped in invocation_expression with
        member_access_expression as the target.
        Example: Console.WriteLine("hello") -> member_access_expression: Console.WriteLine
        """
        # Find member_access_expression child
        for child in call_node.children:
            if child.type == "member_access_expression":
                # Get the full text of member_access_expression
                if child.text:
                    return str(child.text.decode(cs.ENCODING_UTF8))
        return None

    def _resolve_csharp_method_call(
        self, call_node: Node, module_qn: str
    ) -> tuple[str, str] | None:
        """Resolve C# method calls similar to Java's resolve_java_method_call.

        Extracts method name and object from invocation_expression.
        Also ensures StdlibClass is created for the containing class.
        """
        if call_node.type != "invocation_expression":
            return None

        # Try to get full call name directly from node text
        full_call_name = None
        if call_node.text:
            full_call_name = str(call_node.text.decode(cs.ENCODING_UTF8))

        if not full_call_name:
            # Fallback to _get_call_target_name
            full_call_name = self._get_call_target_name(call_node)

        if not full_call_name:
            return None

        # Check if it's a known C# stdlib first
        stdlib_key = None
        if full_call_name in cs.CSHARP_STDLIB_METHODS:
            stdlib_key = full_call_name
        else:
            # Try substring matching
            for key in cs.CSHARP_STDLIB_METHODS.keys():
                if key.lower() in full_call_name.lower():
                    stdlib_key = key
                    break

        if stdlib_key:
            # Extract class name from method (e.g., "Console.WriteLine" -> "Console")
            class_name = stdlib_key.split(".")[0] if "." in stdlib_key else None
            if class_name:
                # Create StdlibClass for the containing class
                stdlib_class_qn = f"csharp.stdlib.{class_name}"
                self._ensure_stdlib_node(
                    stdlib_class_qn, class_name, cs.SupportedLanguage.CSHARP
                )

            # Return stdlib method info
            return (cs.NodeLabel.STDLIB_METHOD, f"csharp.stdlib.{stdlib_key}")

        return None

    def _ingest_function_calls(
        self,
        caller_node: Node,
        caller_qn: str,
        caller_type: str,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
        class_context: str | None = None,
    ) -> None:
        calls_query = queries[language].get(cs.QUERY_CALLS)
        if not calls_query:
            return

        local_var_types = self._resolver.type_inference.build_local_variable_type_map(
            caller_node, module_qn, language
        )

        cursor = QueryCursor(calls_query)
        captures = cursor.captures(caller_node)
        call_nodes = captures.get(cs.CAPTURE_CALL, [])

        logger.debug(
            ls.CALL_FOUND_NODES.format(
                count=len(call_nodes), language=language, caller=caller_qn
            )
        )

        for call_node in call_nodes:
            if not isinstance(call_node, Node):
                continue

            call_name = self._get_call_target_name(call_node)
            if not call_name:
                continue

            # (H) Determine if this is a Java or C# method invocation
            is_java_method_invocation = (
                language == cs.SupportedLanguage.JAVA
                and call_node.type == cs.TS_METHOD_INVOCATION
            )
            is_csharp_invocation = (
                language == cs.SupportedLanguage.CSHARP
                and call_node.type
                in ("invocation_expression", "member_invocation_expression")
            )

            # Step 1: Try to resolve the call
            if is_java_method_invocation:
                callee_info = self._resolver.resolve_java_method_call(
                    call_node, module_qn, local_var_types
                )
            elif is_csharp_invocation:
                # Use dedicated C# method resolver
                callee_info = self._resolve_csharp_method_call(call_node, module_qn)
            else:
                # Default: try resolve_function_call
                callee_info = self._resolver.resolve_function_call(
                    call_name, module_qn, local_var_types, class_context
                )

            # (H) C#: Try to extract full call name from AST for stdlib check
            # Use _get_call_target_name which handles method calls
            if is_csharp_invocation:
                # Try _get_call_target_name first
                full_call_name = self._get_call_target_name(call_node)

                # Also try _extract_csharp_call_name as fallback
                if not full_call_name:
                    full_call_name = self._extract_csharp_call_name(call_node)

                if full_call_name:
                    # Check if it's a known C# stdlib - try exact match AND substring match
                    stdlib_key = None
                    if full_call_name in cs.CSHARP_STDLIB_METHODS:
                        stdlib_key = full_call_name
                    else:
                        # Try substring matching (e.g., "Console.WriteLine" matches key)
                        for key in cs.CSHARP_STDLIB_METHODS.keys():
                            if (
                                key.lower() in full_call_name.lower()
                                or full_call_name.lower() in key.lower()
                            ):
                                stdlib_key = key
                                break

                    if stdlib_key:
                        # Create stdlib node even if resolved (to ensure proper labeling)
                        stdlib_qn = f"csharp.stdlib.{stdlib_key}"
                        self._ensure_stdlib_node(
                            stdlib_qn, stdlib_key, cs.SupportedLanguage.CSHARP
                        )

            # Step 2: If resolved, check if it's a stdlib and create nodes
            if callee_info:
                callee_type, callee_qn = callee_info

                # (H) Check if it's a known stdlib method - create stdlib nodes for Java/C#
                if language in (cs.SupportedLanguage.JAVA, cs.SupportedLanguage.CSHARP):
                    # Try to find stdlib key from callee_qn (the resolved qualified name)
                    stdlib_key = self._find_stdlib_key_from_qn(callee_qn, language)

                    if stdlib_key:
                        self._ensure_stdlib_node(callee_qn, stdlib_key, language)

                # Create relationship for resolved call
                self.ingestor.ensure_relationship_batch(
                    (caller_type, cs.KEY_QUALIFIED_NAME, caller_qn),
                    cs.RelationshipType.CALLS,
                    (callee_type, cs.KEY_QUALIFIED_NAME, callee_qn),
                )
                continue  # Skip to next call

            # Step 3: If not resolved, try builtin/stdlib resolution
            # For Java/C#, use full_call_name to match stdlib patterns
            builtin_call_name = call_name
            if language in (cs.SupportedLanguage.JAVA, cs.SupportedLanguage.CSHARP):
                # Try to get full call name (e.g., "stream.map") for better stdlib matching
                full_call_name = self._get_call_target_name(call_node)
                if full_call_name:
                    builtin_call_name = full_call_name

            if builtin_info := self._resolver.resolve_builtin_call(
                builtin_call_name, language
            ):
                callee_type, callee_qn = builtin_info

                # Java/C#: Create stdlib nodes and relationships
                if language in (cs.SupportedLanguage.JAVA, cs.SupportedLanguage.CSHARP):
                    # Build full call name from AST for stdlib matching
                    full_call_name = self._get_call_target_name(call_node)

                    # Try multiple formats to find stdlib key
                    stdlib_methods = (
                        cs.JAVA_STDLIB_METHODS
                        if language == cs.SupportedLanguage.JAVA
                        else cs.CSHARP_STDLIB_METHODS
                    )

                    # Find stdlib key
                    stdlib_key = self._find_stdlib_key(
                        full_call_name, call_name, stdlib_methods
                    )

                    if stdlib_key:
                        self._ensure_stdlib_node(callee_qn, stdlib_key, language)
                # JavaScript/TypeScript: giữ nguyên behavior - vẫn tạo relationship
                elif language in (cs.SupportedLanguage.JS, cs.SupportedLanguage.TS):
                    pass  # JS/TS: tạo relationship như cũ, không skip
            elif operator_info := self._resolver.resolve_cpp_operator_call(
                call_name, module_qn
            ):
                callee_type, callee_qn = operator_info
            else:
                continue
            logger.debug(
                ls.CALL_FOUND.format(
                    caller=caller_qn,
                    call_name=call_name,
                    callee_type=callee_type,
                    callee_qn=callee_qn,
                )
            )

            self.ingestor.ensure_relationship_batch(
                (caller_type, cs.KEY_QUALIFIED_NAME, caller_qn),
                cs.RelationshipType.CALLS,
                (callee_type, cs.KEY_QUALIFIED_NAME, callee_qn),
            )

    def _build_nested_qualified_name(
        self,
        func_node: Node,
        module_qn: str,
        func_name: str,
        lang_config: LanguageSpec,
    ) -> str | None:
        path_parts: list[str] = []
        current = func_node.parent

        if not isinstance(current, Node):
            logger.warning(
                ls.CALL_UNEXPECTED_PARENT.format(
                    node=func_node, parent_type=type(current)
                )
            )
            return None

        while current and current.type not in lang_config.module_node_types:
            if current.type in lang_config.function_node_types:
                if name_node := current.child_by_field_name(cs.FIELD_NAME):
                    text = name_node.text
                    if text is not None:
                        path_parts.append(text.decode(cs.ENCODING_UTF8))
            elif current.type in lang_config.class_node_types:
                return None

            current = current.parent

        path_parts.reverse()
        if path_parts:
            return f"{module_qn}{cs.SEPARATOR_DOT}{cs.SEPARATOR_DOT.join(path_parts)}{cs.SEPARATOR_DOT}{func_name}"
        return f"{module_qn}{cs.SEPARATOR_DOT}{func_name}"

    def _is_method(self, func_node: Node, lang_config: LanguageSpec) -> bool:
        return is_method_node(func_node, lang_config)
