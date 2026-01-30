# run: python imagination_insider.py [folder]
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from app import ImaginationInsider


def _config_dir() -> Path:
    # config lives in ~/.imagination_insider
    return Path.home() / ".imagination_insider"


def _last_folder_path() -> Path:
    return _config_dir() / "last_folder.txt"


def _read_last_folder() -> Path | None:
    p = _last_folder_path()
    if not p.exists():
        return None
    s = p.read_text(encoding="utf-8", errors="replace").strip()
    return Path(s).expanduser().resolve() if s else None


def _write_last_folder(folder: Path) -> None:
    # persist folder for next time
    _config_dir().mkdir(parents=True, exist_ok=True)
    _last_folder_path().write_text(str(folder), encoding="utf-8")


def main(argv: List[str]) -> int:
    # no folder arg = use last one or default
    if len(argv) < 2:
        folder = _read_last_folder() or (Path.home() / "imagination_insider" / "game_logs")
    else:
        folder = Path(argv[1]).expanduser().resolve()

    if not folder.exists() or not folder.is_dir():
        print(f"error: not a folder: {folder}")
        return 2

    _write_last_folder(folder)
    app = ImaginationInsider(folder)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
