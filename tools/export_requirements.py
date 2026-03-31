# tools/export_requirements.py
from __future__ import annotations
import os
import re
import sys
from pathlib import Path

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    from importlib_metadata import version, PackageNotFoundError  # type: ignore


IMPORT_RE = re.compile(r"^\s*(import|from)\s+([a-zA-Z0-9_\.]+)")


# Some imports are stdlib or internal; ignore them here
STDLIB_GUESS = {
    "os","sys","re","json","time","math","random","typing","dataclasses","pathlib",
    "zipfile","shutil","tempfile","logging","collections","itertools","functools",
    "subprocess","threading","asyncio","traceback"
}

# Map top-level import name -> pip package name (common mismatches)
IMPORT_TO_PKG = {
    "dotenv": "python-dotenv",
    "PIL": "Pillow",
}


def iter_py_files(root: Path):
    for p in root.rglob("*.py"):
        yield p


def collect_imports(root: Path) -> set[str]:
    mods: set[str] = set()
    for py in iter_py_files(root):
        try:
            text = py.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue
        for line in text:
            m = IMPORT_RE.match(line)
            if not m:
                continue
            mod = m.group(2).split(".")[0]
            if mod and mod not in STDLIB_GUESS:
                mods.add(mod)
    return mods


def resolve_versions(mods: set[str]) -> list[str]:
    reqs = []
    for mod in sorted(mods):
        pkg = IMPORT_TO_PKG.get(mod, mod)
        try:
            ver = version(pkg)
            reqs.append(f"{pkg}=={ver}")
        except PackageNotFoundError:
            # might be internal module or not installed
            # keep as comment to help debugging
            reqs.append(f"# {pkg} (not found)")
    return reqs


def main():
    src_root = Path(__file__).resolve().parents[1]
    project_root = src_root.parent
    if not src_root.exists():
        print(f"ERROR: cannot find {src_root}")
        sys.exit(1)

    mods = collect_imports(src_root)
    reqs = resolve_versions(mods)

    out1 = project_root / "requirements.project.txt"
    out1.write_text("\n".join(reqs) + "\n", encoding="utf-8")

    # full environment lock
    # fallback: use pip freeze output
    print("Wrote:", out1)
    print("Tip: also run `python -m pip freeze > requirements.lock.txt` for full lock.")


if __name__ == "__main__":
    main()
