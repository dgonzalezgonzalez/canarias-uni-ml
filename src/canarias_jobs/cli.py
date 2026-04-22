from __future__ import annotations

import sys

from src.canarias_uni_ml.cli import main


def run() -> int:
    argv = sys.argv[1:]
    if argv and argv[0] not in {"jobs", "degrees", "embed"}:
        if "--daemon" in argv:
            translated = ["jobs", "daemon", *[arg for arg in argv if arg != "--daemon"]]
        else:
            translated = ["jobs", "scale" if "--scale" in argv or "--sce-only" in argv else "scrape", *argv]
        argv = translated
    return main(argv)


if __name__ == "__main__":
    raise SystemExit(run())
