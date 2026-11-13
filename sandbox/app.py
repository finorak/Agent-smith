import ast
import subprocess
from ast import Module

from models import SandboxConfig, SandboxError
from node_visitor import NodeVisitor
from sandbox_test import SandboxTest
from script import code_prompt


class Sandbox(SandboxConfig):
    def __init__(
        self,
        image: str = "python:3.13-slim",
    ) -> None:
        super().__init__()
        self._image: str = image
        self._sandbox_tester: SandboxTest = SandboxTest(self)
        self._node_visitor: NodeVisitor = NodeVisitor()

    def _repl(self, codes: list[str]) -> str:
        if codes and codes[-1].rstrip().endswith(":"):
            return "..."
        return ">>>"

    def run(self) -> str | None:
        codes: list[str] = []
        while True:
            try:
                line = input(self._repl(codes))
            except EOFError:
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

    def _import_is_valid(
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
            import_modules: list[str] = self._extract_imports(module)
        for node in import_modules:
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
        return non_authorized

    def _check_code(self, code: str) -> bool:
        module: Module = ast.parse(code)
        non_authorized_imports: list[str] = self._import_is_valid(module)
        self._node_visitor.imports.clear()
        if non_authorized_imports:
            raise SandboxError(
                f"Use of non authorized imports: {non_authorized_imports}"
            )
        return True

    def execute(self, code: str) -> str:
        if not code:
            raise ValueError("Code is empty.")
        print("\nExecuting...")
        self._check_code(code)
        runtime_imports: list[str] = self._sandbox_tester.get_runtime_imports(code)
        non_authorized_imports: list[str] = self._import_is_valid(
            ast.parse(code), runtime_imports
        )
        if non_authorized_imports:
            raise SandboxError(
                f"Use of non authorized imports: {non_authorized_imports}"
            )
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
            "--cpus=1",  # this should be enabled but
            # since the pc at school doesn't suport
            # we will live it as is for now.
            "--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=32m",
            "--ipc=private",
            self._image,
            "python",
            "-",
        ]
        # mounting allowd directory
        for allowed_dir in self.allowed_directories:
            cmd.extend(["-v", f"{allowed_dir}:{allowed_dir}:rw"])
        try:
            task = subprocess.run(
                cmd,
                input=code_prompt(code),
                capture_output=True,
                text=True,
                check=False,
                timeout=self.max_execution_time_seconds,
            )
            return f"""\
stdout: {task.stdout.strip()}
stderr: {task.stderr.strip()}
status: {task.returncode}\n"""
        except subprocess.TimeoutExpired:
            return f"""\
stdout: ""
stderr: Task exced timeout: {self.max_execution_time_seconds}
status: -1\n"""
