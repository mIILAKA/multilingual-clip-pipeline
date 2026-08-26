"""公開用JSON形式の読み込み処理。"""

from __future__ import annotations

import json
from pathlib import Path

from .models import Project

MAX_PROJECT_BYTES = 1_000_000


def load_project(path: Path) -> Project:
    """UTF-8のJSONファイルを検証可能なプロジェクトへ変換する。"""

    if path.stat().st_size > MAX_PROJECT_BYTES:
        raise ValueError("project JSON の上限は1MBです")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("project JSON のルートはオブジェクトである必要があります")
    return Project.from_dict(payload)
