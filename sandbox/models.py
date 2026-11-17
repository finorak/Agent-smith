from pydantic import BaseModel, ConfigDict, Field


class SandboxConfig(BaseModel):
    """Sandbox configuration for student solutions.
    Uses allowlist approach: only imports in authorized_imports are allowed.
    Everything else is blocked by default.
    """

    model_config = ConfigDict(extra="allow")

    authorized_imports: list[str] = Field(
        default_factory=lambda: [
            "time",
            "math",
            "math.*",
            "collections",
            "collections.*",
            "itertools",
            "re",
            "json",
            "typing",
            "typing.*",
            "functools",
            "operator",
            "heapq",
            "bisect",
            "copy",
            "string",
            "random",
            "datetime",
            "datetime.*",
            "array",
            "cmath",
        ]
    )
    allowed_directories: list[str] = Field(
        default_factory=lambda: ["/home/finorako/project/Agent-smith/tmp/testbed", "/home/finorako/project/Agent-smith/tmp/agent"]
    )
    max_execution_time_seconds: int = 10000
    max_memory_mb: int = 50


class SandboxError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class FinalAnswer(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
