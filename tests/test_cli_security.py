import json
from pathlib import Path

from clip_pipeline.cli import main


def test_demo_rejects_source_path_outside_media_directory(
    tmp_path: Path, capsys
) -> None:
    project_path = tmp_path / "project.json"
    project_path.write_text(
        json.dumps(
            {
                "title": "Traversal attempt",
                "cuts": [{"source": "../outside.mp4", "start": 0, "end": 1}],
                "subtitles": [],
            }
        ),
        encoding="utf-8",
    )

    result = main(["demo", "--project", str(project_path), "--root", str(tmp_path)])

    assert result != 0
    assert "media" in capsys.readouterr().err
    assert not (tmp_path.parent / "outside.mp4").exists()


def test_demo_rejects_output_path_outside_output_directory(
    tmp_path: Path, capsys
) -> None:
    project_path = tmp_path / "project.json"
    project_path.write_text(
        json.dumps(
            {
                "title": "Output traversal attempt",
                "cuts": [
                    {"source": "media/source.mp4", "start": 0, "end": 1}
                ],
                "subtitles": [],
            }
        ),
        encoding="utf-8",
    )

    result = main(
        [
            "demo",
            "--project",
            str(project_path),
            "--root",
            str(tmp_path),
            "--output",
            "../outside.mp4",
        ]
    )

    assert result != 0
    assert "output" in capsys.readouterr().err
    assert not (tmp_path.parent / "outside.mp4").exists()


def test_demo_force_is_required_to_replace_generated_files(
    tmp_path: Path, capsys
) -> None:
    project_path = tmp_path / "project.json"
    project_path.write_text(
        json.dumps(
            {
                "title": "Overwrite guard",
                "cuts": [{"source": "media/source.mp4", "start": 0, "end": 1}],
                "subtitles": [],
            }
        ),
        encoding="utf-8",
    )
    arguments = [
        "demo",
        "--project",
        str(project_path),
        "--root",
        str(tmp_path),
        "--output",
        "output/demo.mp4",
    ]

    assert main(arguments) == 0
    assert main(arguments) == 2
    assert "上書きしません" in capsys.readouterr().err
    assert main([*arguments, "--force"]) == 0
