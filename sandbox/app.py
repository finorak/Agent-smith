import ast
import subprocess
import sys
from ast import Module
from typing import Any

from node_visitor import NodeVisitor
from sandbox_config import SandboxConfig
from utils import basic_error_handler, show_log


class Sandbox(SandboxConfig):
    def __init__(self) -> None:
        """Initialize a Sandbox class instance."""
        super().__init__()

    # TODO: All the print in this function need to be sent to
    # the appropriate person/server so that the LLM can find
    # a new solution based on what we found.
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
            try:
                module = ast.parse(code)  # code is valid or not.
            except SyntaxError as e:
                show_log(e, file=sys.stderr)
                continue
            import_valid, non_authorized_imports = self._import_is_valid(module)
            if not import_valid:
                show_log(
                    f"Use of non authorized imports: {non_authorized_imports}."
                    " Code can't be executed"
                )
                continue
            result = self.run_code(code)
            show_log(result)

    # TODO: make this function return a json
    # containing the stdout, stderr, and exit code
    # Might add something other than that later on.
    def run_code(self, code: str) -> dict[str, Any]:
        """Run untrusted code inside a docker.

        Given a code, we don't simply trust it
        and run it on the host machine, we use
        a docker as a security layer to prevent
        malicious code to run avock in our machine.

        Args:
            code (str): The code we need to run.
        """
        cmd: list[str] = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=64",
            f"--memory={self.max_memory_mb}m",
            "--cpus=1",
            "--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=32",
            "--ipc=private",
            "python:3.13-slim",
            "python",
            "-",
        ]
        try:
            result = subprocess.run(
                cmd,
                input=code,
                capture_output=True,
                text=True,
                timeout=self.max_execution_time_seconds,
                check=False,
            )
            return {
                "output": result.stdout,
                "error": result.stderr,
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired as e:
            return {
                "output": e.stderr or "",
                "error": e.stderr or "",
                "exit_code": -1,
            }

    def _import_is_valid(self, module: Module) -> tuple[bool, list[str]]:
        """Validate given code's Import.

        Given a code, we Validate against our rules if it's valid or not.

        Args:
            code (Module): the code to verify.
        Returns:
            imports: (tuplle[bool, list[str]): A tuple where the \
first value tell us if it's valid or not, the second the non authorized \
imporsts.
        """
        non_authorized: list[str] = []
        modules: list[str] = self._extract_imports(module)
        # TODO: replace this for loop with `any`
        # Or we can still use this, we don't care.
        for node in modules:
            module_valid: bool = False
            for authorized in self.authorized_imports:
                authorized = authorized.rstrip(".*")
                removed_prefix = node.removeprefix(authorized)
                # Verify if the module imported is valid or not.
                if node in authorized or (
                    node.startswith(authorized)
                    and len(removed_prefix) >= 1
                    and removed_prefix[0] == "."
                ):
                    module_valid = True
                    break
            if not module_valid:
                non_authorized.append(node)
        return (not non_authorized, non_authorized)

    def _extract_imports(self, module: Module) -> list[str]:
        """Extract imports from the given code.

        We extract all imports from the given code so
        that we can verify if the code given follow
        our rules or not.

        Args:
            module (Module): The code we have to extract the imports.
        """
        extractor = NodeVisitor()
        extractor.visit(module)
        return [module for module in extractor.imports]
