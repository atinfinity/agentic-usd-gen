"""Blender をバックグラウンドで呼び出す。"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

SCRIPTS = Path(__file__).parent / "blender"
CANDIDATES = ["/Applications/Blender.app/Contents/MacOS/Blender"]


def find_blender(explicit: str | None = None) -> str:
    for c in [explicit, os.environ.get("BLENDER"), shutil.which("blender"), *CANDIDATES]:
        if c and Path(c).exists():
            return c
    raise FileNotFoundError("Blender が見つかりません。--blender か環境変数 BLENDER で指定してください")


def run_script(blender: str, script: str, *args: str | Path, log_path: Path | None = None) -> None:
    cmd = [blender, "-b", "--factory-startup", "--python-exit-code", "1", "--python", str(SCRIPTS / script), "--",
           *map(str, args)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if log_path:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr)
    if proc.returncode != 0:
        tail = "\n".join((proc.stdout + proc.stderr).splitlines()[-30:])
        raise RuntimeError(f"Blender の実行に失敗しました（{script}）:\n{tail}")
