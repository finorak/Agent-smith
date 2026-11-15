import subprocess
from typing import Any

from .models import SandboxError
from .script import code_audit
from .settings import SANDBOX_CONTAINER


class SandboxTest:
    def __init__(self, parent: Any) -> None:
        self._parent = parent

    def runtime_code_checker(self, code: str, wrappers: dict[str, str]) -> list[str]:
        if not code:
            raise ValueError("Code is empty.")
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
            f"--memory={self._parent.max_memory_mb}m",
            f"--memory-swap={self._parent.max_memory_mb}m",
            "--cpus=1",  # this should be enabled but
            "--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=32m",
            "-v",
            "/tmp/ipc_socket/:/ipc:rw",
            "--ipc=private",
            self._parent._image,
            "python",
            "-",
        ]
        try:
            task = subprocess.run(
                cmd,
                input=code_audit(code, wrappers),
                capture_output=True,
                text=True,
                check=False,
                timeout=self._parent.max_execution_time_seconds,
            )
            prefix: str = "__SANDBOXIMPORT__:"
            if task.returncode == 137:
                raise SandboxError("Memory limit reached. Can't continue")
            return [
                module.strip()[len(prefix) :]
                for module in task.stderr.split("\n")
                if module.strip().startswith(prefix)
            ]
        except subprocess.TimeoutExpired:
            raise RuntimeError("Couldn't finish task due to time error")
        except subprocess.SubprocessError:
            raise SandboxError("An error occured during imports extraction")
