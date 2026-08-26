from pathlib import Path

from clip_pipeline.io import load_project
from clip_pipeline.validation import validate_project


def test_public_example_passes_preflight() -> None:
    project = load_project(Path("examples/project.json"))

    assert validate_project(project) == []
