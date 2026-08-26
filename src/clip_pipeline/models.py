"""パイプラインで共有する、外部依存のないデータモデル。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Cut:
    """元動画から採用する半開区間を表す。"""

    source: Path
    start: float
    end: float

    @property
    def duration(self) -> float:
        """カットの長さを秒で返す。"""

        return self.end - self.start

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Cut:
        """JSON互換の辞書からカットを生成する。"""

        return cls(
            source=Path(value["source"]),
            start=float(value["start"]),
            end=float(value["end"]),
        )


@dataclass(frozen=True)
class Subtitle:
    """元動画時刻に置かれた字幕を表す。"""

    start: float
    end: float
    text: str
    track: str = "dialogue"

    @property
    def duration(self) -> float:
        """字幕の表示時間を秒で返す。"""

        return self.end - self.start

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Subtitle:
        """JSON互換の辞書から字幕を生成する。"""

        return cls(
            start=float(value["start"]),
            end=float(value["end"]),
            text=str(value["text"]),
            track=str(value.get("track", "dialogue")),
        )


@dataclass(frozen=True)
class Project:
    """1本の切り抜きに必要な構造化データを保持する。"""

    title: str
    language: str
    cuts: tuple[Cut, ...]
    subtitles: tuple[Subtitle, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> Project:
        """JSON互換の辞書からプロジェクトを生成する。"""

        return cls(
            title=str(value["title"]),
            language=str(value.get("language", "auto")),
            cuts=tuple(Cut.from_dict(item) for item in value.get("cuts", [])),
            subtitles=tuple(
                Subtitle.from_dict(item) for item in value.get("subtitles", [])
            ),
        )


@dataclass(frozen=True)
class ValidationIssue:
    """機械検査で見つかった1件の問題を表す。"""

    code: str
    message: str
    severity: str = "error"
