"""
Module used to identify if the program is safe to use or not
by using a simple AST check.
"""

import ast
from ast import Call, Import, ImportFrom
from typing import Any


class NodeVisitor(ast.NodeVisitor):
    """Node Visitor to form our tree.


    Given a code source, we run an AST checker on it
    to verify if the code is safe to use or not.
    """

    def __init__(self) -> None:
        """Initialize a `NodeVisitor` instance."""
        self.imports: set[str] = set()

    def visit_Import(self, node: Import) -> Any:
        """Check import statemant.

        Given a node, we extract all import statement
        from it.

        Args:
            node (ast.Import): the node to traverse.
        """
        for import_module in node.names:
            import_form = import_module.name
            self.imports.add(import_form)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ImportFrom) -> Any:
        """Check relative import statemant.

        Given a node, we extract all relative import statement
        from it.

        Args:
            node (ast.Import): the node to traverse.
        """
        module_name = node.module
        for from_module in node.names:
            import_form = from_module.name
            self.imports.add(f"{module_name}.{import_form}")
        self.generic_visit(node)

    def visit_Call(self, node: Call) -> Any:
        if isinstance(node.func, ast.Name):
            print(f"Function called: {node.func.id}")
        elif isinstance(node.func, ast.Attribute):
            print(f"Method called: {node.func.attr}")

