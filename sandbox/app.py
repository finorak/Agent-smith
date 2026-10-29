import ast
import sys

from utils import basic_error_handler, show_log


class Sandbox:
    def __init__(self) -> None:
        """Initialize a Sandbox class instance."""

    @basic_error_handler
    def run(self) -> None:
        """Run Sandbox program.

        Reading from the stding we extract the code given
        by user and verify if it's valid or not, if yes, we
        execute it in our Sandbox else not.
        """
        running: bool = True
        while running:
            show_log(">>>", end=" ")
            code: str = sys.stdin.readline().rstrip("\n")
            if code in ("exit", "quit"):
                show_log("\n😬Thanks for using our solution")
                return
            if not self._code_is_valid(code):
                print()

    def _code_is_valid(self, code: str) -> bool:
        """Validate given code.

        Given a code, we Validate against our rules if it
        is valid or not.

        Args:
            code (str): the code to verify.
        """
        self._extract_imports(code)
        return True

    def _extract_imports(self, code: str) -> list[str]:
        """Extract imports from the given code.

        We extract all imports from the given code so
        that we can verify if the code given follow
        our rules or not.

        Args:
            code (str): The code we have to extract the imports.
        """
        parse = ast.parse(code)
        _ = parse
        return []
