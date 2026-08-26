"""パイプラインの構造と検査を手元で確認するCLI。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .io import load_project
from .render import create_synthetic_source, probe_duration, render_project, resolve_sources
from .validation import validate_project
from .workflow import build_workflow


def _parser() -> argparse.ArgumentParser:
    """CLI引数の定義を返す。"""

    parser = argparse.ArgumentParser(prog="clip-pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="project JSONを機械検査する")
    validate.add_argument("project", type=Path)

    plan = subparsers.add_parser("plan", help="制作工程と承認ゲートを表示する")
    plan.add_argument("--approved-for-final", action="store_true")

    demo = subparsers.add_parser("demo", help="合成動画でE2Eパイプラインを実行する")
    demo.add_argument("--project", type=Path, default=Path("examples/project.json"))
    demo.add_argument("--root", type=Path, default=Path("."))
    demo.add_argument("--output", type=Path, default=Path("output/synthetic-demo.mp4"))
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLIを実行し、成功時0・検査失敗時1を返す。"""

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    if args.command == "validate":
        project = load_project(args.project)
        issues = validate_project(project)
        if not issues:
            print(f"OK: {project.title} — 検査項目に問題はありません")
            return 0
        for issue in issues:
            print(f"{issue.severity.upper()} [{issue.code}] {issue.message}")
        return 1

    if args.command == "demo":
        project = load_project(args.project)
        issues = validate_project(project)
        if issues:
            for issue in issues:
                print(f"{issue.severity.upper()} [{issue.code}] {issue.message}")
            return 1
        resolved = resolve_sources(project, args.root.resolve())
        sources = {cut.source for cut in resolved.cuts}
        if len(sources) != 1:
            print("ERROR: 合成デモは1つのソース動画だけを扱います")
            return 1
        source = next(iter(sources))
        create_synthetic_source(source, duration=max(cut.end for cut in resolved.cuts) + 1.0)
        output = args.output if args.output.is_absolute() else args.root / args.output
        render_project(resolved, output)
        print(f"OK: {output} ({probe_duration(output):.2f} 秒)")
        return 0

    stages = build_workflow(approved_for_final=args.approved_for_final)
    for number, stage in enumerate(stages, 1):
        owner = "automatic" if stage.automatic else "human gate"
        print(f"{number:02d}. {stage.name:<20} [{owner}] {stage.purpose}")
    if not args.approved_for_final:
        print("STOP: 最終書き出しには人の承認が必要です")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
