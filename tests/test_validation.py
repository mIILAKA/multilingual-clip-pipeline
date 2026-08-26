import math
from pathlib import Path

from clip_pipeline.models import Cut, Project, Subtitle
from clip_pipeline.validation import display_width, validate_project


def test_display_width_distinguishes_full_and_half_width_text() -> None:
    assert display_width("字幕AB") == 3.0


def test_valid_project_has_no_issues() -> None:
    project = Project(
        title="Synthetic demo",
        language="en",
        cuts=(Cut(Path("sample.mp4"), 10.0, 20.0),),
        subtitles=(Subtitle(11.0, 13.0, "短い字幕"),),
    )

    assert validate_project(project) == []


def test_validator_reports_independent_failures() -> None:
    project = Project(
        title="Broken demo",
        language="en",
        cuts=(
            Cut(Path("sample.mp4"), 10.0, 20.0),
            Cut(Path("sample.mp4"), 19.0, 25.0),
        ),
        subtitles=(
            Subtitle(11.0, 11.5, "短すぎる字幕"),
            Subtitle(12.0, 13.0, "これは一秒では読めないほど長い日本語字幕です"),
            Subtitle(30.0, 32.0, "カット外"),
            Subtitle(12.5, 14.0, "重なる字幕"),
        ),
    )

    codes = {issue.code for issue in validate_project(project)}

    assert codes == {
        "overlapping-cuts",
        "short-subtitle",
        "reading-speed",
        "subtitle-outside-cuts",
        "overlapping-subtitles",
    }


def test_validator_rejects_non_finite_times_and_partial_subtitles() -> None:
    project = Project(
        title="Unsafe demo",
        language="en",
        cuts=(
            Cut(Path("sample.mp4"), math.nan, 5.0),
            Cut(Path("sample.mp4"), 10.0, 20.0),
        ),
        subtitles=(Subtitle(9.5, 11.0, "partly outside"),),
    )

    codes = {issue.code for issue in validate_project(project)}

    assert "invalid-cut" in codes
    assert "subtitle-outside-cuts" in codes


def test_validator_finds_non_adjacent_duplicate_source_ranges() -> None:
    project = Project(
        title="Duplicate ranges",
        language="en",
        cuts=(
            Cut(Path("sample.mp4"), 10.0, 20.0),
            Cut(Path("sample.mp4"), 30.0, 40.0),
            Cut(Path("sample.mp4"), 15.0, 18.0),
        ),
        subtitles=(),
    )

    codes = {issue.code for issue in validate_project(project)}

    assert "overlapping-cuts" in codes
