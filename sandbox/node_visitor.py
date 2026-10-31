"""
Module used to identify if the program is safe to use or not
by using a simple AST check.
"""

import ast
from ast import Import, ImportFrom
from typing import Any, Self


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
            if import_module.asname:
                import_form = f"{import_module.name} as {import_module.asname}"
            self.imports.add(f"import {import_form}")
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
            if from_module.asname:
                import_form = f"{from_module.name} as {from_module.asname}"
            self.imports.add(f"from {module_name} import {import_form}")
        self.generic_visit(node)

    @staticmethod
    def is_authorized(module_name: str, authorized_module: set[str]) -> bool:
        if module_name in authorized_module:
            return True
        for module in authorized_module:
            if module_name.startswith(module_name.rstrip(".")):
                return True
        return False
