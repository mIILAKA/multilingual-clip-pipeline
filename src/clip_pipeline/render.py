"""FFmpegを使った、著作物不要の最小E2Eレンダリング。"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .models import Cut, Project


def _require_binary(name: str) -> str:
    """必要な外部コマンドの絶対パスを返す。"""

    executable = shutil.which(name)
    if executable is None:
        raise RuntimeError(f"{name} がPATHにありません")
    return executable


def _run(command: list[str]) -> None:
    """外部コマンドを実行し、失敗時に読める例外を送出する。"""

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[-8:]
        raise RuntimeError("外部コマンドに失敗しました:\n" + "\n".join(detail))


def create_synthetic_source(path: Path, *, duration: float) -> None:
    """テストパターンと正弦波だけで合成ソース動画を生成する。"""

    if duration <= 0:
        raise ValueError("duration は0より大きい必要があります")
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            _require_binary("ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=30",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000",
            "-t",
            f"{duration:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ]
    )


def resolve_sources(project: Project, root: Path) -> Project:
    """相対ソースパスを指定されたルート基準の絶対パスへ変換する。"""

    cuts = tuple(
        Cut(
            source=cut.source if cut.source.is_absolute() else root / cut.source,
            start=cut.start,
            end=cut.end,
        )
        for cut in project.cuts
    )
    return Project(project.title, project.language, cuts, project.subtitles)


def render_project(project: Project, output: Path) -> None:
    """1つのソースから指定カットを切り出し、順番どおりに結合する。"""

    if not project.cuts:
        raise ValueError("1つ以上のカットが必要です")
    sources = {cut.source.resolve() for cut in project.cuts}
    if len(sources) != 1:
        raise ValueError("公開デモのレンダラーは1つのソース動画だけを扱います")
    source = next(iter(sources))
    if not source.exists():
        raise FileNotFoundError(source)

    filters: list[str] = []
    inputs: list[str] = []
    for index, cut in enumerate(project.cuts):
        filters.append(
            f"[0:v]trim=start={cut.start:.6f}:end={cut.end:.6f},"
            f"setpts=PTS-STARTPTS[v{index}]"
        )
        filters.append(
            f"[0:a]atrim=start={cut.start:.6f}:end={cut.end:.6f},"
            f"asetpts=PTS-STARTPTS[a{index}]"
        )
        inputs.append(f"[v{index}][a{index}]")
    filters.append(
        "".join(inputs)
        + f"concat=n={len(project.cuts)}:v=1:a=1[outv][outa]"
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            _require_binary("ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[outv]",
            "-map",
            "[outa]",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            str(output),
        ]
    )


def probe_duration(path: Path) -> float:
    """ffprobeで動画の長さを秒として取得する。"""

    result = subprocess.run(
        [
            _require_binary("ffprobe"),
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return float(result.stdout.strip())
