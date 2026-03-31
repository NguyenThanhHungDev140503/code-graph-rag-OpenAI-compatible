from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...types_defs import ASTNode


LINQ_CLAUSE_TO_METHOD = {
    "from_clause": "SelectMany",
    "where_clause": "Where",
    "select_clause": "Select",
    "orderby_clause": "OrderBy",
    "group_clause": "GroupBy",
    "join_clause": "Join",
    "let_clause": "Select",
}


class LinqQueryAnalyzer:
    def __init__(self, type_inference):
        self.type_inference = type_inference

    def parse_query_expression(self, node: "ASTNode") -> dict[str, Any]:
        result: dict[str, Any] = {
            "source": None,
            "clauses": [],
            "lambda_params": {},
            "resolved_calls": [],
        }
        if node is None or node.type != "query_expression":
            return result
        from_clause = node.child_by_field_name("from")
        if from_clause:
            source_node = from_clause.child_by_field_name("in")
            if source_node:
                text_bytes = getattr(source_node, "text", None)
                result["source"] = text_bytes.decode() if text_bytes else None
            identifier = from_clause.child_by_field_name("identifier")
            if identifier:
                text_bytes = getattr(identifier, "text", None)
                param_name = text_bytes.decode() if text_bytes else None
                if param_name:
                    result["lambda_params"][param_name] = {
                        "clause": "from",
                        "node": from_clause,
                    }
        for child in node.children:
            if child.type in LINQ_CLAUSE_TO_METHOD:
                clause_info = self._analyze_clause(child)
                if clause_info:
                    result["clauses"].append(clause_info)
        return result

    def _analyze_clause(self, clause_node: "ASTNode") -> dict[str, Any] | None:
        clause_type = clause_node.type
        method_name = LINQ_CLAUSE_TO_METHOD.get(clause_type)
        if not method_name:
            return None
        resolved_method = self.type_inference.resolve_linq_expression(method_name)
        if not resolved_method:
            resolved_method = f"csharp.stdlib.Linq.{method_name}"
        return {
            "type": clause_type,
            "method": method_name,
            "resolved_method": resolved_method,
            "node": clause_node,
        }

    def extract_lambda_variables(self, query_node: "ASTNode") -> dict[str, str]:
        variables: dict[str, str] = {}
        if query_node is None or query_node.type != "query_expression":
            return variables
        for child in query_node.children:
            if child.type == "from_clause":
                identifier = child.child_by_field_name("identifier")
                if identifier:
                    text_bytes = getattr(identifier, "text", None)
                    if text_bytes:
                        variables[text_bytes.decode()] = "source_element"
            elif child.type in ("let_clause", "join_clause"):
                identifier = child.child_by_field_name("identifier")
                if identifier:
                    text_bytes = getattr(identifier, "text", None)
                    if text_bytes:
                        variables[text_bytes.decode()] = "let_element"
        return variables

    def resolve_query_methods(self, query_node: "ASTNode") -> list[str]:
        methods = []
        parsed = self.parse_query_expression(query_node)
        for clause in parsed["clauses"]:
            if clause["resolved_method"]:
                methods.append(clause["resolved_method"])
        return methods
