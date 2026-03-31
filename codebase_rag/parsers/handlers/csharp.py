from __future__ import annotations

from typing import TYPE_CHECKING

from ... import constants as cs
from .base import BaseLanguageHandler

if TYPE_CHECKING:
    from ...types_defs import ASTNode


class CSharpHandler(BaseLanguageHandler):
    def extract_decorators(self, node: ASTNode) -> list[str]:
        return []

    def build_method_qualified_name(
        self,
        class_qn: str,
        method_name: str,
        method_node: ASTNode,
    ) -> str:
        return f"{class_qn}{cs.SEPARATOR_DOT}{method_name}"

    def process_query_expression(self, node: ASTNode) -> dict[str, ASTNode]:
        clauses = {}
        for child in node.children:
            child_type = child.type
            if child_type == "from_clause":
                clauses["from"] = child
            elif child_type == "where_clause":
                clauses["where"] = child
            elif child_type == "select_clause":
                clauses["select"] = child
            elif child_type == "orderby_clause":
                clauses["orderby"] = child
            elif child_type == "group_clause":
                clauses["group"] = child
            elif child_type == "join_clause":
                clauses["join"] = child
            elif child_type == "let_clause":
                clauses["let"] = child
        return clauses
