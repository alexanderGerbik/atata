from enum import Enum
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from . import ffmpeg, subtitles
from .ranges import prepare_ranges
from .structures import Options, Range
from .playlist import generate_playlist


class Mode(str, Enum):
    ata = "ata"
    at = "at"
    ta = "ta"


def main():
    return typer.run(_main)


def _main(
    source_video: Annotated[
        Path,
        typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ],
    mode: Mode = Mode.ata,
    sub_index: int = None,
    sub_path: Annotated[
        Optional[Path],
        typer.Option(
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
            resolve_path=True,
        ),
    ] = None,
    dialog_gap_seconds: int = 5,
    max_dialog_duration_seconds: int = 30,
):
    metadata = ffmpeg.get_metadata(source_video)
    assert sub_index is None or 0 < sub_index <= metadata.subtitle_stream_count
    assert sub_index is None or sub_path is None

    options = Options(
        dialog_gap_seconds,
        max_dialog_duration_seconds,
        create_prefix=mode.value.startswith("a"),
        create_suffix=mode.value.endswith("a"),
    )
    suffix = get_suffix(options)
    playlist_path = source_video.parent / f"{source_video.stem}{suffix}.xspf"

    if sub_path is None:
        if sub_index is None:
            sub_index = metadata.subtitle_stream_count
        sub_path = source_video.parent / f"{source_video.stem}{suffix}.srt"
        ffmpeg.extract_subtitles(source_video, sub_path, sub_index-1)

    ranges = subtitles.process_subtitles(sub_path, options)
    ranges = prepare_ranges(ranges, metadata.duration, options)
    generate_playlist(ranges, source_video, sub_path, metadata.duration, playlist_path)


def get_suffix(options: Options):
    a = "a" if options.create_prefix else ""
    b = "a" if options.create_suffix else ""
    return f".{a}t{b}"
