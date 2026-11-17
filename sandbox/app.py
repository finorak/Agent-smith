# **************************************************************************** #
#                                                                              #
#                                                         :::      ::::::::    #
#    app.py                                             :+:      :+:    :+:    #
#                                                     +:+ +:+         +:+      #
#    By: finorako <finorako@student.42antananarivo  +#+  +:+       +#+         #
#                                                 +#+#+#+#+#+   +#+            #
#    Created: 2026/11/11 10:02:19 by megalonia         #+#    #+#              #
#    Updated: 2026/11/15 06:12:06 by megalonia        ###   ########.fr        #
#                                                                              #
# **************************************************************************** #

import ast
import atexit
import os
import subprocess
import threading
import time
import traceback
from ast import Module
from typing import Any

from .models import SandboxConfig, SandboxError
from .node_visitor import NodeVisitor
from .sandbox_test import SandboxTest
from .script import code_prompt
from .settings import (
    DOCKER_SOCKET_PATH,
    DOCKET_SOCKET_DIR,
    HOST_SOCKET_DIR,
    SANDBOX_CONTAINER,
)
from .utils import cleanup, connection_handler


class Sandbox(SandboxConfig):
    """Sandbox class."""

    def __init__(
        self,
        image: str = "python:3.13-slim",
        wrappers: dict[str, str] | Any = None,
        mcp_url: str | None = None,
        tool_caller: Any = None,
    ) -> None:
        super().__init__()
        self._image: str = image
        self._sandbox_tester: SandboxTest = SandboxTest(self)
        self._node_visitor: NodeVisitor = NodeVisitor()
        self._wrappers = wrappers
        self._code_len: int = 1024 * 1024
        self._mcp_url: str | None = mcp_url
        self._tool_caller = tool_caller

    def _repl(self, codes: list[str]) -> str:
        if codes:
            if not codes[-1]:
                return ">>>"
            if codes[-1].rstrip().endswith(":"):
                return "..."
            if codes[-1][0] != "_" and not codes[-1][0].isalpha():
                return "..."
        return ">>>"

    def _handle_state(self, start_time: float) -> bool:
        curr = time.perf_counter()
        return curr - start_time < self.max_execution_time_seconds

    def run(self) -> str | None:
        codes: list[str] = []
        print("Ctrl+D or exit to execute...")
        while True:
            try:
                line = input(self._repl(codes))
            except EOFError:
                break
            if line.strip() in ("exit", "END"):
                break
            codes.append(line)
        return self.execute("\n".join(codes))

    def _extract_imports(self, module: Module) -> list[str]:
        """Extract imports from the given code.

        We extract all imports from the given code so
        that we can verify if the code given follow
        our rules or not.

        Args:
            module (Module): The code we have to extract the imports.
        """
        self._node_visitor.visit(module)
        imports = self._node_visitor.imports.copy()
        self._node_visitor.imports.clear()
        return [module for module in imports]

    # TODO: this function has bug in verifying the imported
    # stuff, will fix it later.
    def _get_non_authorized_imports(
        self, module: Module, import_mod: list[str] | None = None
    ) -> list[str]:
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
        if import_mod:
            import_modules = import_mod
        else:
            import_modules = self._extract_imports(module)
        for node in import_modules:
            module_valid: bool = False
            for authorized in self.authorized_imports:
                authorized = authorized.rstrip(".*")
                if node == authorized:
                    module_valid = True
                    break
            if not module_valid:
                non_authorized.append(node)
        self._node_visitor.imports.clear()
        return non_authorized

    def _static_code_check(self, module: Module) -> bool:
        non_authorized_imports: list[str] = self._get_non_authorized_imports(module)
        if non_authorized_imports:
            raise SandboxError(
                f"Use of non authorized imports: {non_authorized_imports}"
            )
        return True

    def execute(self, code: str) -> str:
        if not code:
            raise ValueError("Code is empty.")
        try:
            module: Module = ast.parse(code)
        # TODO: format the output extracted from this
        # to only show the error from the code not
        # the whole errors
        except SyntaxError:
            return f"\nstdout: ''\nstderr: {traceback.format_exc()}\nstatus: 1"
        print("\nExecuting...")
        self._static_code_check(module)
        runtime_imports: list[str] = self._sandbox_tester.runtime_code_checker(
            code, self._wrappers
        )
        non_authorized_imports: list[str] = self._get_non_authorized_imports(
            module, runtime_imports
        )
        if non_authorized_imports:
            raise SandboxError(
                f"Use of non authorized imports: {non_authorized_imports}"
            )
        os.chmod(HOST_SOCKET_DIR, 0o711)
        event_start: threading.Event = threading.Event()
        thread: threading.Thread | None = None
        start: float = time.perf_counter()
        if self._mcp_url:
            thread = threading.Thread(
                target=connection_handler,
                args=(
                    lambda: self._handle_state(start),
                    self._mcp_url,
                    self._tool_caller,
                    event_start,
                ),
                daemon=True,
            )
            thread.start()
        if not event_start.wait(5):
            raise RuntimeError("MCP server failed to connect.")

        cmd: list[str] = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--name",
            SANDBOX_CONTAINER,
            "--network=none",
            "--read-only",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit=64",
            f"--memory={self.max_memory_mb}m",
            f"--memory-swap={self.max_memory_mb}m",
            # "--cpus=1",
            "--user=65534:65534",
            "--ipc=private",
            "-v",
            f"{HOST_SOCKET_DIR}:{DOCKET_SOCKET_DIR}:rw",
            "-v",
            os.path.abspath(self.allowed_directories[1]),
            "-w",
            f"{os.path.abspath(self.allowed_directories[0])}:/workdir",
        ]

        for allowed_dir in self.allowed_directories:
            cmd.extend(["-v", f"{allowed_dir}:{allowed_dir}:rw"])
        cmd.extend([self._image, "python", "-"])
        try:
            runner = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            atexit.register(cleanup, process=runner)
            stdout, stderr = runner.communicate(
                input=code_prompt(code, self._wrappers, DOCKER_SOCKET_PATH),
                timeout=self.max_execution_time_seconds,
            )
            return f"""\
stdout: {stdout}
stderr: {stderr}
status: {runner.returncode}\n"""
        except subprocess.TimeoutExpired:
            return f"""\
stdout: ""
stderr: Task exced timeout: {self.max_execution_time_seconds}
status: -1\n"""
