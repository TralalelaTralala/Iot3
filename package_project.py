"""Create a portable source archive, excluding caches and local secrets."""
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "iot3_project.zip"
SKIP_DIRS = {".pio", ".venv", "__pycache__", ".git"}
SKIP_FILES = {"config.json", ARCHIVE.name}

with ZipFile(ARCHIVE, "w", ZIP_DEFLATED) as zf:
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.name in SKIP_FILES:
            continue
        relative = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        zf.write(path, relative.as_posix())

print(f"Created {ARCHIVE} ({ARCHIVE.stat().st_size} bytes)")
