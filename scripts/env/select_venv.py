#!/usr/bin/env python3
"""
Resolve / create the per-platform virtual environment for hidock-next.
Restores the missing scripts/env/select_venv.py that setup-windows.bat and
setup-unix.sh expect (issue #41).

Contract:
  --print           Print the absolute venv path if it exists; otherwise no output.
  --ensure          Create the venv at the platform-appropriate path if missing.
  --ensure --print  Create (if missing) and print the absolute path.
"""

import argparse
import os
import shutil
import sys
import venv
from pathlib import Path

MIN_PYTHON = (3, 10)


def venv_dir_name() -> str:
    if sys.platform.startswith("win"):
        return ".venv.win"
    if sys.platform == "darwin":
        return ".venv.mac"
    return ".venv.nix"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def venv_path() -> Path:
    return repo_root() / venv_dir_name()


def venv_python(path: Path) -> Path:
    if sys.platform.startswith("win"):
        return path / "Scripts" / "python.exe"
    return path / "bin" / "python"


def existing_venv_version(path: Path):
    cfg = path / "pyvenv.cfg"
    if not cfg.exists():
        return None
    for line in cfg.read_text().splitlines():
        if line.strip().startswith("version"):
            _, _, value = line.partition("=")
            parts = value.strip().split(".")
            try:
                return (int(parts[0]), int(parts[1]))
            except (IndexError, ValueError):
                return None
    return None


def venv_is_valid(path: Path) -> bool:
    if not venv_python(path).exists():
        return False
    version = existing_venv_version(path)
    return version is not None and version >= MIN_PYTHON


def ensure(path: Path) -> None:
    if venv_is_valid(path):
        return
    if path.exists():
        # Existing venv predates the MIN_PYTHON requirement (or its version
        # can't be determined) - rebuild it with the current interpreter.
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    builder = venv.EnvBuilder(with_pip=True, clear=False, upgrade=False, symlinks=(os.name != "nt"))
    builder.create(str(path))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ensure", action="store_true")
    parser.add_argument("--print", dest="do_print", action="store_true")
    args = parser.parse_args()

    path = venv_path()

    if args.ensure:
        try:
            ensure(path)
        except Exception as exc:
            print(f"ERROR: failed to create venv at {path}: {exc}", file=sys.stderr)
            return 1

    if args.do_print and venv_is_valid(path):
        print(str(path))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
