import argparse


def parse_argument() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    group = parser.add_argument_group()
    group.add_argument("--mcp-stdio", default=None)
    group.add_argument("--mcp-server", default=None)
    parser.add_argument("template", nargs=1)
    return parser.parse_args()
