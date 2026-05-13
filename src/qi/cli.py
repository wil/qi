"""CLI entry point for Qi."""

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="qi", description="Qi - a no-nonsense coding agent"
    )
    parser.add_argument("--version", action="version", version="0.1.0")
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
