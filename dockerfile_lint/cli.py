"""dockerfile-lint [FILE ...] [--strict] [--ignore CODE] [--json]"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import lint


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="dockerfile-lint", description="Offline Dockerfile hygiene and security checks.")
    p.add_argument("files", nargs="*", default=["Dockerfile"])
    p.add_argument("--strict", action="store_true", help="warnings fail the run")
    p.add_argument("--ignore", action="append", default=[], metavar="CODE", help="skip a rule code, e.g. DL010 (repeatable)")
    p.add_argument("--json", action="store_true")
    p.add_argument("--version", action="version", version=__version__)
    args = p.parse_args(argv)
    failed = False
    results = {}
    for file in args.files:
        try:
            text = Path(file).read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            print(f"dockerfile-lint: {exc.strerror}: {file}", file=sys.stderr)
            return 2
        ignored = {c.strip().upper() for c in args.ignore}
        findings = [f for f in lint(text) if f.code not in ignored]
        results[file] = findings
        if any(f.level == "error" for f in findings) or (args.strict and any(f.level == "warning" for f in findings)):
            failed = True
    if args.json:
        print(json.dumps({f: [x.__dict__ for x in fs] for f, fs in results.items()}, indent=2, ensure_ascii=False))
    else:
        for file, findings in results.items():
            if not findings:
                print(f"{file}: OK")
            for x in findings:
                print(f"{file}:{x.line}: [{x.level.upper()}] {x.code} {x.message}")
    return 1 if failed else 0
