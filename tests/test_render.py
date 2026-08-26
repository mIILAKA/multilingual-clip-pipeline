from pathlib import Path

import pytest

from clip_pipeline.models import Cut, Project
from clip_pipeline.render import (
    create_synthetic_source,
    probe_duration,
    render_project,
)


def test_ffmpeg_demo_renders_selected_cuts(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    output = tmp_path / "clip.mp4"
    create_synthetic_source(source, duration=4.0)
    project = Project(
        title="E2E demo",
        language="en",
        cuts=(
            Cut(source, 0.5, 1.5),
            Cut(source, 2.0, 3.5),
        ),
        subtitles=(),
    )

    render_project(project, output)

    assert output.exists()
    assert output.stat().st_size > 0
    assert probe_duration(output) == pytest.approx(2.5, abs=0.15)


def test_renderer_rejects_multiple_source_files(tmp_path: Path) -> None:
    project = Project(
        title="Unsupported demo",
        language="en",
        cuts=(
            Cut(tmp_path / "a.mp4", 0.0, 1.0),
            Cut(tmp_path / "b.mp4", 0.0, 1.0),
        ),
        subtitles=(),
    )

    with pytest.raises(ValueError, match="1つのソース動画"):
        render_project(project, tmp_path / "output.mp4")


def test_renderer_does_not_overwrite_existing_output_by_default(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    output = tmp_path / "clip.mp4"
    create_synthetic_source(source, duration=2.0)
    output.write_bytes(b"keep-me")
    project = Project(
        title="No overwrite",
        language="en",
        cuts=(Cut(source, 0.0, 1.0),),
        subtitles=(),
    )

    with pytest.raises(FileExistsError):
        render_project(project, output)

    assert output.read_bytes() == b"keep-me"


def test_synthetic_source_has_a_duration_limit(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="上限"):
        create_synthetic_source(tmp_path / "source.mp4", duration=301.0)
