"""公開データだけで再現できる、字幕とカットの決定的な検査。"""

from __future__ import annotations

import unicodedata

from .models import Cut, Project, Subtitle, ValidationIssue


def display_width(text: str) -> float:
    """全角を1、半角を0.5として字幕の視覚的な長さを数える。"""

    return sum(
        1.0 if unicodedata.east_asian_width(char) in {"W", "F", "A"} else 0.5
        for char in text
        if not char.isspace()
    )


def _inside_any_cut(subtitle: Subtitle, cuts: tuple[Cut, ...]) -> bool:
    """字幕が少なくとも1つの採用カットと交差するかを返す。"""

    return any(subtitle.start < cut.end and subtitle.end > cut.start for cut in cuts)


def validate_project(
    project: Project,
    *,
    max_reading_speed: float = 7.0,
    min_subtitle_duration: float = 0.8,
) -> list[ValidationIssue]:
    """制作事故につながる構造上の問題を決定的に検査する。"""

    issues: list[ValidationIssue] = []

    for index, cut in enumerate(project.cuts):
        if cut.start < 0 or cut.end <= cut.start:
            issues.append(
                ValidationIssue("invalid-cut", f"cut[{index}] の開始・終了時刻が不正です")
            )

    for index, (current, following) in enumerate(zip(project.cuts, project.cuts[1:])):
        if current.source == following.source and following.start < current.end:
            issues.append(
                ValidationIssue(
                    "overlapping-cuts",
                    f"cut[{index}] と cut[{index + 1}] が重複しています",
                )
            )

    for index, subtitle in enumerate(project.subtitles):
        if subtitle.duration < min_subtitle_duration:
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

        if not _inside_any_cut(subtitle, project.cuts):
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
        for (left_index, left), (right_index, right) in zip(rows, rows[1:]):
            if right.start < left.end:
                issues.append(
                    ValidationIssue(
                        "overlapping-subtitles",
                        f"track={track} の subtitle[{left_index}] と "
                        f"subtitle[{right_index}] が重複しています",
                    )
                )

    return issues
