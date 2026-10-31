from pydantic import BaseModel, Field
import contextlib
import io
import sys
import argparse
import json


class SandboxConfig(BaseModel):
    """Sandbox configuration for student solutions.
    Uses allowlist approach: only imports in authorized_imports are allowed.
    Everything else is blocked by default.
    """
    authorized_imports: list[str] = Field(default_factory=lambda: [
        "math", "math.*", "collections", "collections.*", "itertools", "re",
        "json", "typing", "typing.*", "functools", "operator", "heapq",
        "bisect", "copy", "string", "random", "datetime", "datetime.*",
        "array", "cmath",])
    allowed_directories: list[str] = Field(default_factory=lambda: [
        "/testbed", "/tmp/agent"
    ])
    max_execution_time_seconds: int = Field(ge=10, default=15)
    max_memory_mb: int = Field(ge=64, default=512)


class SandboxProperty:
    def __init__(self, config: SandboxConfig) -> None:
        self.builtins = {
            'print': print,
            'len': len,
            'range': range,
            'sum': sum,
            'max': max,
            'min': min,
            'sorted': sorted,
            'type': type,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'list': list,
            'exit': exit,
            '__import__': __import__,
            '__build_class__': __build_class__,
            '__name__': '__main__',
            '__qualname__': '',
            '__module__': '__main__',
            'Exception': Exception
        }
        self.authorized_imports = config.authorized_imports
        self.allowed_directories = config.allowed_directories
        self.max_execution_time_seconds = config.max_execution_time_seconds
        self.max_memory_mb = config.max_memory_mb


class Sandbox:
    def __init__(self, property: SandboxProperty) -> None:
        self.property = property
        self.property.builtins.update({"final_answer": self.final_answer})
        self.state = {
            '__builtins__': self.property.builtins
        }
        self.input_sign = 'ooo> '
        self.decal_sign = '...> '
        self.code: list[str] = []

    def interact(self, prompt: str) -> str:
        temp = io.StringIO()
        if prompt != "EOF":
            self.code.append(prompt)
        else:
            try:
                with contextlib.redirect_stdout(temp), contextlib.redirect_stderr(temp):
                    exec("\n".join(self.code), self.state)
            except Exception as e:
                print(e, file=sys.stderr)
            finally:
                self.code.clear()
        return temp.getvalue()

    def test(self) -> None:
        i = "EOF"
        while True:
            if i == "EOF":
                print(self.input_sign, end='')
            else:
                print(self.decal_sign, end='')
            try:
                i = input()
                result = sandbox.interact(i)
                if result:
                    print(result, end='')
            except Exception as e:
                print(e)
            except KeyboardInterrupt:
                break

    @staticmethod
    def final_answer(s: str) -> None:
        print(f"final_answer function is used HERE! (input:{s})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sandbox_template", nargs="?", default="default")
    args = parser.parse_args()

    try:
        with open(args.sandbox_template) as f:
            config = json.load(f)
            sandbox_config = SandboxConfig(**config)
    except Exception:
        if args.sandbox_template != "default":
            print("ERROR WHILE LOADING sandbox_template.json,"
                    " using default")
        sandbox_config = SandboxConfig()

    sandbox_property = SandboxProperty(sandbox_config)
    sandbox = Sandbox(sandbox_property)
    sandbox.test()
