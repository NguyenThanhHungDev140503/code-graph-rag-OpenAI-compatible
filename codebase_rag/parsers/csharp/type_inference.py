from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..factory import ASTCacheProtocol


class CSharpTypeInferenceEngine:
    def __init__(self, ast_cache: "ASTCacheProtocol"):
        self.ast_cache = ast_cache
        self._init_known_library_methods()

    def _init_known_library_methods(self):
        self.known_library_methods = {
            "fluentvalidation": {
                "WithMessage",
                "NotEmpty",
                "NotNull",
                "MaximumLength",
                "MinimumLength",
                "Length",
                "Matches",
                "Email",
                "Url",
                "InclusiveBetween",
                "ExclusiveBetween",
                "GreaterThan",
                "GreaterThanOrEqualTo",
                "LessThan",
                "LessThanOrEqualTo",
                "Must",
                "When",
                "Unless",
                "RuleFor",
                "ForMember",
                "TransformFor",
                "SetValidator",
                "Cascade",
                "WithName",
                "WithState",
                "OverridePropertyName",
                "DependentRules",
            },
            "linq": {
                "Select",
                "Where",
                "First",
                "FirstOrDefault",
                "Single",
                "SingleOrDefault",
                "Any",
                "All",
                "Count",
                "LongCount",
                "Sum",
                "Min",
                "Max",
                "Average",
                "Aggregate",
                "OrderBy",
                "OrderByDescending",
                "ThenBy",
                "ThenByDescending",
                "GroupBy",
                "Join",
                "GroupJoin",
                "Take",
                "Skip",
                "TakeWhile",
                "SkipWhile",
                "Distinct",
                "Union",
                "Intersect",
                "Except",
                "ToList",
                "ToArray",
                "ToDictionary",
                "ToLookup",
                "OfType",
                "Cast",
                "AsEnumerable",
                "AsQueryable",
            },
            "efcore": {
                "HasColumnName",
                "HasMaxLength",
                "IsRequired",
                "IsUnicode",
                "HasPrecision",
                "HasDefaultValue",
                "HasDefaultValueSql",
                "HasComputedColumnSql",
                "IsRowVersion",
                "IsFixedLength",
                "HasForeignKey",
                "HasPrincipalKey",
                "HasIndex",
                "WithMany",
                "WithOne",
                "HasConstraint",
                "OnDelete",
                "OnUpdate",
                "UseSqlite",
                "UseSqlServer",
                "UseNpgsql",
            },
            "mediatr": {
                "Send",
                "Publish",
                "CreateRequest",
                "CreateRequestHandler",
                "WithRequest",
                "WithBehavior",
            },
            "aspnetcore": {
                "MapGet",
                "MapPost",
                "MapPut",
                "MapDelete",
                "MapGroup",
                "MapControllerRoute",
                "Produces",
                "ProducesProblem",
                "ProducesResponseType",
                "WithName",
                "WithMetadata",
                "AllowAnonymous",
                "Authorize",
            },
            "serialization": {
                "JsonPropertyName",
                "JsonIgnore",
                "JsonProperty",
                "Serialize",
                "Deserialize",
                "ToJson",
                "FromJson",
            },
            "logging": {
                "LogInformation",
                "LogWarning",
                "LogError",
                "LogDebug",
                "LogTrace",
                "LogCritical",
                "Log",
            },
            "object": {
                "ToString",
                "Equals",
                "GetHashCode",
                "GetType",
                "MemberwiseClone",
                "ReferenceEquals",
            },
        }
        self.all_known_methods = set()
        for methods in self.known_library_methods.values():
            self.all_known_methods.update(methods)

    def infer_type(self, node, caller_node=None, caller_qn=None):
        if node is None:
            return None
        node_type = node.type if hasattr(node, "type") else str(type(node))
        if node_type == "member_expression":
            member_name = node.text.decode() if hasattr(node, "text") else str(node)
            if caller_qn:
                return self._infer_from_member_access(member_name, caller_qn)
        return None

    def _infer_from_member_access(self, member_name: str, caller_qn: str):
        if member_name in self.all_known_methods:
            for library, methods in self.known_library_methods.items():
                if member_name in methods:
                    # (H) Return without "StdlibMethod." prefix
                    return f"csharp.library.{library}.{member_name}"
        return None

    def is_known_library_method(self, method_name: str) -> bool:
        return method_name in self.all_known_methods

    def get_library_method_type(self, method_name: str) -> str | None:
        if method_name not in self.all_known_methods:
            return None
        for library, methods in self.known_library_methods.items():
            if method_name in methods:
                return library
        return None

    def resolve_method_chain(self, call_name: str, caller_qn: str) -> str | None:
        if "." not in call_name:
            return None
        parts = call_name.split(".")
        method_name = parts[-1]
        if method_name in self.all_known_methods:
            library = self.get_library_method_type(method_name)
            if library:
                # (H) Return without "StdlibMethod." prefix - caller adds it
                return f"csharp.stdlib.{library}.{method_name}"
        return None

    def resolve_linq_expression(self, call_name: str) -> str | None:
        linq_keywords = {
            "where",
            "select",
            "any",
            "all",
            "first",
            "firstordefault",
            "single",
            "singleordefault",
            "count",
            "sum",
            "min",
            "max",
            "average",
            "aggregate",
            "orderby",
            "orderbydescending",
            "thenby",
            "thenbydescending",
            "groupby",
            "take",
            "skip",
            "distinct",
            "union",
            "tolist",
            "toarray",
        }
        lower_name = call_name.lower()
        for keyword in linq_keywords:
            if keyword in lower_name:
                # (H) Return without "StdlibMethod." prefix - caller adds it
                return f"csharp.stdlib.Linq.{keyword.title()}"
        return None

    def resolve_property_access(self, property_name: str, caller_qn: str) -> str | None:
        if caller_qn and "." in caller_qn:
            return f"Property.{caller_qn}.{property_name}"
        return f"Property.{property_name}"

    def resolve_indexer_access(
        self, index_expression: str, caller_qn: str
    ) -> str | None:
        return f"Indexer.{caller_qn}[]"

    def resolve_async_call(self, call_name: str) -> str | None:
        async_keywords = {
            "Task.Run",
            "Task.FromResult",
            "Task.Delay",
            "ExecuteAsync",
            "SendAsync",
            "PublishAsync",
            "GetAsync",
            "PostAsync",
            "PutAsync",
            "DeleteAsync",
        }
        for keyword in async_keywords:
            if keyword.lower() in call_name.lower():
                return f"StdlibMethod.csharp.stdlib.Async.{keyword}"
        return None

    def resolve_constructor_call(self, type_name: str) -> str | None:
        if type_name.startswith("new "):
            type_name = type_name[4:].strip()
        return f"Constructor.{type_name}"

    def is_property_access(self, call_name: str) -> bool:
        property_patterns = [
            r"^[a-z][a-zA-Z0-9]*$",
        ]
        import re

        for pattern in property_patterns:
            if re.match(pattern, call_name) and not call_name[0].isupper():
                return True
        return False

    def is_indexer_access(self, call_name: str) -> bool:
        return "[" in call_name and "]" in call_name

    def is_async_call(self, call_name: str) -> bool:
        async_indicators = ["async", "await", "Task", "Promise"]
        return any(
            indicator.lower() in call_name.lower() for indicator in async_indicators
        )
