"""人の確認ゲートを含む、実運用由来の工程定義。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkflowStage:
    """工程名と、その工程が担保する性質を表す。"""

    name: str
    purpose: str
    automatic: bool = True


def build_workflow(*, approved_for_final: bool = False) -> tuple[WorkflowStage, ...]:
    """承認状態に応じた、実行可能な工程一覧を返す。"""

    stages = [
        WorkflowStage("prepare-job", "カット・字幕・話者情報を構造化する"),
        WorkflowStage("normalize-timeline", "余白、読速、字幕重複を決定的に補正する"),
        WorkflowStage("render-preview", "1080pの確認用動画を生成する"),
        WorkflowStage("align-to-speech", "字幕時刻を音声と語境界へ照合する"),
        WorkflowStage("preflight", "公開前の機械検査を一括実行する"),
        WorkflowStage("human-review", "内容・翻訳・演出を人が通して確認する", automatic=False),
    ]
    if approved_for_final:
        stages.extend(
            [
                WorkflowStage("render-final", "承認済みの内容を最終解像度で書き出す"),
                WorkflowStage("sync-manifest", "成果物のハッシュと投稿情報を同期する"),
            ]
        )
    return tuple(stages)
