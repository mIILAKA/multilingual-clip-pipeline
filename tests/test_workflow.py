from clip_pipeline.workflow import build_workflow


def test_final_render_is_hidden_before_human_approval() -> None:
    names = [stage.name for stage in build_workflow(approved_for_final=False)]

    assert "human-review" in names
    assert "render-final" not in names
    assert "sync-manifest" not in names


def test_final_render_is_added_after_human_approval() -> None:
    names = [stage.name for stage in build_workflow(approved_for_final=True)]

    assert names[-2:] == ["render-final", "sync-manifest"]
