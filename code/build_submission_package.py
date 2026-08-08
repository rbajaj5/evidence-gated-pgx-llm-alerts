"""Build the capstone submission ZIP and stable SHA256 manifest.

The manifest is generated from the final submission file set. It excludes
historical proposal/progress provenance, ignored runtime artifacts such as
code/results/, render scratch folders, Python caches, LaTeX build products, the
manifest itself, and the ZIP.
Text files are normalized to LF before hashing so a fresh clone on another
platform verifies cleanly.
"""

from __future__ import annotations

import csv
import hashlib
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = PROJECT_ROOT / "MANIFEST_SHA256.csv"
PACKAGE = PROJECT_ROOT / "package" / "Module_14_Capstone_Pruned_Evidence_Gate_Package_Ravi_Bajaj.zip"

INCLUDED_ROOT_FILES = {
    ".gitattributes",
    ".gitignore",
    "README.md",
    "RELEASE_NOTES.md",
    "REPRODUCIBILITY.md",
    "requirements.txt",
    "SAFETY.md",
}

INCLUDED_DIRS = {
    "code",
    "figures",
    "paper",
    "results",
    "summary",
    "supplement",
}

EXCLUDED_DIR_NAMES = {
    "__pycache__",
    ".pytest_cache",
    "_audit_text",
    "_pdf_qa",
    "_rendered",
    "package",
}

EXCLUDED_SUFFIXES = {
    ".aux",
    ".bbl",
    ".blg",
    ".fdb_latexmk",
    ".fls",
    ".log",
    ".out",
    ".pyc",
    ".pyo",
    ".synctex.gz",
    ".tmp",
}

BINARY_SUFFIXES = {".docx", ".pdf", ".png", ".zip"}


def posix_rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def is_text_file(path: Path) -> bool:
    return path.suffix.lower() not in BINARY_SUFFIXES


def excluded(path: Path) -> bool:
    rel = path.relative_to(PROJECT_ROOT)
    parts = rel.parts
    if path == MANIFEST or path == PACKAGE:
        return True
    if any(part in EXCLUDED_DIR_NAMES for part in parts):
        return True
    if len(parts) >= 2 and parts[0] == "code" and parts[1] == "results":
        return True
    name = path.name.lower()
    if any(name.endswith(suffix) for suffix in EXCLUDED_SUFFIXES):
        return True
    if len(parts) == 1:
        return parts[0] not in INCLUDED_ROOT_FILES
    return parts[0] not in INCLUDED_DIRS


def normalize_text_file(path: Path) -> None:
    if not is_text_file(path):
        return
    raw = path.read_bytes()
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    if normalized != raw:
        path.write_bytes(normalized)


def iter_manifest_files() -> list[Path]:
    files: list[Path] = []
    for path in PROJECT_ROOT.rglob("*"):
        if path.is_file() and not excluded(path):
            normalize_text_file(path)
            files.append(path)
    return sorted(files, key=posix_rel)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(files: list[Path]) -> None:
    rows = []
    for path in files:
        data = path.read_bytes()
        rows.append(
            {
                "path": posix_rel(path),
                "bytes": str(len(data)),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )
    with MANIFEST.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256"], lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build_zip(files: list[Path]) -> None:
    PACKAGE.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(PACKAGE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, posix_rel(path))
        archive.write(MANIFEST, MANIFEST.name)


def main() -> None:
    files = iter_manifest_files()
    build_manifest(files)
    build_zip(files)
    print(f"Wrote {MANIFEST.relative_to(PROJECT_ROOT)} with {len(files)} rows")
    print(f"Wrote {PACKAGE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
