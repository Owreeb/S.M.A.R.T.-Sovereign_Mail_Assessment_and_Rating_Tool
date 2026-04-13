from __future__ import annotations

import argparse
import importlib
from collections.abc import Callable


def run_bronze() -> None:
    module = importlib.import_module("src.domainlist_pipline.bronze_pipeline")
    module.run()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scanner command entrypoint")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("run_bronze", help="Run bronze pipeline")
    return parser


def main() -> None:
    command_handlers: dict[str, Callable[[], None]] = {
        "run_bronze": run_bronze,
    }

    parser = build_parser()
    args = parser.parse_args()
    command_handlers[args.command]()


if __name__ == "__main__":
    main()
