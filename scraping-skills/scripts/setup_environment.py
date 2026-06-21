#!/usr/bin/env python3
"""Prepare a Python environment for economic scraping projects."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(command: list[str], dry_run: bool = False) -> None:
    print("+ " + " ".join(command))
    if not dry_run:
        subprocess.run(command, check=True)


def venv_python(venv_dir: Path) -> Path:
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def main() -> int:
    parser = argparse.ArgumentParser(description="Set up Python and Scrapling dependencies.")
    parser.add_argument("--venv", default=".venv")
    parser.add_argument("--install", action="store_true", help="Install Python packages")
    parser.add_argument("--browser-deps", action="store_true", help="Install browser dependencies with scrapling install")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--extras", default="pandas,openpyxl,cryptography", help="Comma-separated additional packages")
    args = parser.parse_args()

    venv_dir = Path(args.venv)
    py = venv_python(venv_dir)
    if not py.exists():
        run([sys.executable, "-m", "venv", str(venv_dir)], dry_run=args.dry_run)
    if not args.dry_run and not py.exists():
        raise RuntimeError(f"Virtual environment python not found: {py}")

    if args.install:
        packages = ['scrapling[all]']
        packages.extend([item.strip() for item in args.extras.split(",") if item.strip()])
        run([str(py), "-m", "pip", "install", "--upgrade", "pip"], dry_run=args.dry_run)
        run([str(py), "-m", "pip", "install", *packages], dry_run=args.dry_run)

    if args.browser_deps:
        run([str(py), "-m", "scrapling", "install", "--force"], dry_run=args.dry_run)

    snapshot = {
        "created_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "venv": str(venv_dir),
        "python": str(py),
        "install_requested": args.install,
        "browser_deps_requested": args.browser_deps,
        "dry_run": args.dry_run,
    }
    Path("environment_snapshot.json").write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    print(json.dumps(snapshot, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
