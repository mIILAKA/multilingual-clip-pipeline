"""FFmpegを使った、著作物不要の最小E2Eレンダリング。"""

from __future__ import annotations

import math
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


MAX_SYNTHETIC_DURATION = 300.0


def _run(command: list[str], *, timeout: float = 120.0) -> None:
    """外部コマンドを実行し、失敗時に読める例外を送出する。"""

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise RuntimeError("外部コマンドが制限時間を超えました") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[-8:]
        raise RuntimeError("外部コマンドに失敗しました:\n" + "\n".join(detail))


def create_synthetic_source(
    path: Path, *, duration: float, overwrite: bool = False
) -> None:
    """テストパターンと正弦波だけで合成ソース動画を生成する。"""

    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("duration は有限かつ0より大きい必要があります")
    if duration > MAX_SYNTHETIC_DURATION:
        raise ValueError(f"duration の上限は {MAX_SYNTHETIC_DURATION:.0f} 秒です")
    if path.exists() and not overwrite:
        raise FileExistsError(f"既存ファイルは上書きしません: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            _require_binary("ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y" if overwrite else "-n",
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


def render_project(project: Project, output: Path, *, overwrite: bool = False) -> None:
    """1つのソースから指定カットを切り出し、順番どおりに結合する。"""

    if not project.cuts:
        raise ValueError("1つ以上のカットが必要です")
    if len(project.cuts) > 100:
        raise ValueError("カット数の上限は100件です")
    if any(
        not math.isfinite(cut.start)
        or not math.isfinite(cut.end)
        or cut.start < 0
        or cut.end <= cut.start
        for cut in project.cuts
    ):
        raise ValueError("カットの開始・終了時刻が不正です")
    sources = {cut.source.resolve() for cut in project.cuts}
    if len(sources) != 1:
        raise ValueError("公開デモのレンダラーは1つのソース動画だけを扱います")
    source = next(iter(sources))
    if not source.exists():
        raise FileNotFoundError(source)
    if output.resolve() == source:
        raise ValueError("入力動画と出力動画には別のパスを指定してください")
    if output.exists() and not overwrite:
        raise FileExistsError(f"既存ファイルは上書きしません: {output}")

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
            "-y" if overwrite else "-n",
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
        timeout=30.0,
    )
    return float(result.stdout.strip())
