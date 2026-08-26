"""公開データだけで再現できる、字幕とカットの決定的な検査。"""

from __future__ import annotations

import math
import unicodedata
from itertools import combinations, pairwise

from .models import Cut, Project, Subtitle, ValidationIssue


def display_width(text: str) -> float:
    """全角を1、半角を0.5として字幕の視覚的な長さを数える。"""

    return sum(
        1.0 if unicodedata.east_asian_width(char) in {"W", "F", "A"} else 0.5
        for char in text
        if not char.isspace()
    )


def _inside_any_cut(subtitle: Subtitle, cuts: tuple[Cut, ...]) -> bool:
    """字幕全体が少なくとも1つの有効な採用カット内にあるかを返す。"""

    return any(
        math.isfinite(cut.start)
        and math.isfinite(cut.end)
        and cut.start <= subtitle.start
        and subtitle.end <= cut.end
        for cut in cuts
    )


def validate_project(
    project: Project,
    *,
    max_reading_speed: float = 7.0,
    min_subtitle_duration: float = 0.8,
) -> list[ValidationIssue]:
    """制作事故につながる構造上の問題を決定的に検査する。"""

    if not math.isfinite(max_reading_speed) or max_reading_speed <= 0:
        raise ValueError("max_reading_speed は有限の正数である必要があります")
    if not math.isfinite(min_subtitle_duration) or min_subtitle_duration <= 0:
        raise ValueError("min_subtitle_duration は有限の正数である必要があります")

    issues: list[ValidationIssue] = []

    if not project.title.strip():
        issues.append(ValidationIssue("missing-title", "title が空です"))
    if not project.cuts:
        issues.append(ValidationIssue("missing-cuts", "1つ以上のカットが必要です"))
    if len(project.cuts) > 100:
        issues.append(ValidationIssue("too-many-cuts", "カット数の上限は100件です"))
    if len(project.subtitles) > 5_000:
        issues.append(ValidationIssue("too-many-subtitles", "字幕数の上限は5,000件です"))

    for index, cut in enumerate(project.cuts):
        if (
            not math.isfinite(cut.start)
            or not math.isfinite(cut.end)
            or cut.start < 0
            or cut.end <= cut.start
        ):
            issues.append(
                ValidationIssue("invalid-cut", f"cut[{index}] の開始・終了時刻が不正です")
            )

    for (left_index, left), (right_index, right) in combinations(
        enumerate(project.cuts), 2
    ):
        valid_times = all(
            math.isfinite(value)
            for value in (left.start, left.end, right.start, right.end)
        )
        overlaps = left.start < right.end and right.start < left.end
        if valid_times and left.source == right.source and overlaps:
            issues.append(
                ValidationIssue(
                    "overlapping-cuts",
                    f"cut[{left_index}] と cut[{right_index}] が重複しています",
                )
            )

    for index, subtitle in enumerate(project.subtitles):
        valid_times = (
            math.isfinite(subtitle.start)
            and math.isfinite(subtitle.end)
            and subtitle.start >= 0
            and subtitle.end > subtitle.start
        )
        if not valid_times:
            issues.append(
                ValidationIssue(
                    "invalid-subtitle",
                    f"subtitle[{index}] の開始・終了時刻が不正です",
                )
            )
        elif subtitle.duration < min_subtitle_duration:
            issues.append(
                ValidationIssue(
                    "short-subtitle",
                    f"subtitle[{index}] の表示時間が {subtitle.duration:.2f} 秒です",
                )
            )
        elif display_width(subtitle.text) / subtitle.duration > max_reading_speed:
            speed = display_width(subtitle.text) / subtitle.duration
            issues.append(
                ValidationIssue(
                    "reading-speed",
                    f"subtitle[{index}] の読速が {speed:.1f} 字/秒です",
                )
            )

        if not subtitle.text.strip():
            issues.append(
                ValidationIssue("empty-subtitle", f"subtitle[{index}] の本文が空です")
            )
        elif len(subtitle.text) > 500:
            issues.append(
                ValidationIssue(
                    "subtitle-too-long", f"subtitle[{index}] の本文が500文字を超えています"
                )
            )

        if not valid_times or not _inside_any_cut(subtitle, project.cuts):
            issues.append(
                ValidationIssue(
                    "subtitle-outside-cuts",
                    f"subtitle[{index}] が採用カットの外にあります",
                )
            )

    by_track: dict[str, list[tuple[int, Subtitle]]] = {}
    for index, subtitle in enumerate(project.subtitles):
        by_track.setdefault(subtitle.track, []).append((index, subtitle))
    for track, rows in by_track.items():
        rows.sort(key=lambda item: item[1].start)
        for (left_index, left), (right_index, right) in pairwise(rows):
            if (
                all(
                    math.isfinite(value)
                    for value in (left.start, left.end, right.start, right.end)
                )
                and right.start < left.end
            ):
                issues.append(
                    ValidationIssue(
                        "overlapping-subtitles",
                        f"track={track} の subtitle[{left_index}] と "
                        f"subtitle[{right_index}] が重複しています",
                    )
                )

    return issues
