import subprocess
from typing import Any

from models import SandboxError
from script import code_audit


class SandboxTest:
    def __init__(self, parent: Any) -> None:
        self._parent = parent

    def get_runtime_imports(self, code: str) -> list[str]:
        if not code:
            raise ValueError("Code is empty.")
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
            f"--memory={self._parent.max_memory_mb}m",
            "--cpus=1",  # this should be enabled but
            # since the pc at school doesn't suport
            # we will live it as is for now.
            "--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=32m",
            "--ipc=private",
            self._parent._image,
            "python",
            "-",
        ]
        try:
            task = subprocess.run(
                cmd,
                input=code_audit(code),
                capture_output=True,
                text=True,
                check=False,
                timeout=self._parent.max_execution_time_seconds,
            )
            prefix: str = "__SANDBOXIMPORT__:"
            return [
                module[len(prefix) :]
                for module in task.stdout.split("\n")
                if module.startswith(prefix)
            ]
        except subprocess.TimeoutExpired:
            raise RuntimeError("Couldn't finish task due to time error")
        except subprocess.SubprocessError:
            raise SandboxError("An error occured during imports extraction")
