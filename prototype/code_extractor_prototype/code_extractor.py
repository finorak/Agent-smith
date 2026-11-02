class CodeExtractor:
    def __init__(self) -> None:
        self.start = '```'
        self.end = '```'

    def extract_code(self, llm_output: str) -> str:
        if self.start not in llm_output or self.end not in llm_output:
            return ""
        parts = llm_output.split(self.start, 1)
        if len(parts) < 2:
            return ""
        code_content = parts[1].split(self.end, 1)[0]
        return code_content
