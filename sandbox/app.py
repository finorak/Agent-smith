import ast
import asyncio
import re
import subprocess
import sys
from ast import Module
from typing import Any

from mcp import CallToolRequest

from .node_visitor import NodeVisitor
from .sandbox_model import SandboxModel
from .utils import basic_error_handler, show_log


class Sandbox(SandboxModel):
    """A secure execution environment for running tools and \
routines.

    This class initializes an isolated sandbox environment \
designed to interface with external tools by accepting and \
executing a specified runtime routine.

    Attributes:
        routine (str): The configuration string, script, or \
sequence of commands defining the execution steps for the tool.
    """

    def __init__(self, client_routine: Any = None, server_url: str = "") -> None:
        """Initialize a Sandbox class instance.

        Args:
            routine (str): The configuration string, script, or sequence \
of commands defining the execution steps for the tool.
        """
        super().__init__()
        self._extractor = NodeVisitor()
        self._curr_code = ""
        self.client_routine = client_routine
        self.server_url = server_url

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
            import_valid, non_authorized = self._import_is_valid(module)
            if not import_valid:
                show_log(
                    f"Use of non authorized imports: {non_authorized}."
                    " Code can't be executed"
                )
                continue
            result = self.execute(code)
            if result:
                show_log(result)

    # TODO: make this function return a json
    # containing the stdout, stderr, and exit code
    # Might add something other than that later on.
    def execute(self, code: str) -> dict[str, Any] | None:
        """Run untrusted code inside a docker.

        Given a code, we don't simply trust it
        and run it on the host machine, we use
        a docker as a security layer to prevent
        malicious code to run avock in our machine.

        Args:
            code (str): The code we need to run.
        """
        params: list[Any] | None = self._extract_parmeters(code)
        res: CallToolRequest | Any = asyncio.run(
            self.client_routine(
                server_url=self.server_url,
                tool_name=self._remove_paranthesies(code),
                args=params,
            )
        )
        if res and not res.content[0].text.startswith("Unknown tool"):
            return {
                "output": res.content[0].text if not res.is_error else "",
                "error": res.content[0].text if res.is_error else "",
                "exit_code": 1 if res.is_error else 0,
            }
        self._curr_code += f"\n{code}"
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
            # "--cpus=1",  # this should be enabled but
            # since the pc at school doesn't suport
            # we will live it as is for now.
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
                "output": e.stderr,
                "error": e.stderr,
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
        self._extractor.visit(module)
        imports = self._extractor.imports.copy()
        self._extractor.imports.clear()
        return [module for module in imports]

    def _extract_parmeters(self, code: str) -> list[str] | None:
        """Extract parameters from the gieven code.

        Args:
            code (str): the code we want to extract it's \
parameters.

        Returns:
            params (list[str] | None): parameters of the tools.
        """
        raw_args: list[str] | None = None
        match = re.search(r"\((.*?)\)", code)
        if not match:
            return None
        raw_args = [arg.strip() for arg in match.group(1).split(",")]
        typed_args: list[Any] = []
        for arg in raw_args:
            try:
                typed_args.append(ast.literal_eval(arg))
            except Exception:
                typed_args.append(arg)
        return typed_args

    def _remove_paranthesies(self, code: str) -> str | None:
        """Remove parantezised from the given code.

        As we only send the name of the tool to the
        server, we don't need to send how we call the
        tool, so we remove the parenthesis from the given
        code before sending it to our server.

        Args:
            code (str): the code we want to send to \
our server.

        Returns:
            tool_name (str | None): the name of the tool.
        """
        first_index: int = code.find("(")
        if first_index < 0:
            return None
        return code[0:first_index].strip()
