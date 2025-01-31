import itertools
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List

import ffmpeg

from .structures import Range


@dataclass
class VideoMetaData:
    duration: float
    video_stream_count: int
    audio_stream_count: int
    subtitle_stream_count: int


def concat(sources: List[Path], destination: Path):
    with tempfile.NamedTemporaryFile(suffix=".txt") as temp_file:
        Path(temp_file.name).write_text("".join(f"file '{s.resolve()}'\n" for s in sources))
        (
            ffmpeg.input(temp_file.name, f="concat", safe="0")
            .output(str(destination), c="copy")
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )


def cut_scenes(source_path: Path, destination_path: Path, scenes: List[Range], audio_index: int):
    input = ffmpeg.input(source_path)
    n = len(scenes)
    video = input.video
    audio = input[f'a:{audio_index}']
    vsplits = video.filter_multi_output('split', n)
    vcuts = [vs.filter("select", f"gte(t,{start})*lt(t,{end})").filter("setpts", "PTS-STARTPTS") for vs, (start, end) in zip(vsplits, scenes)]
    asplits = audio.filter_multi_output('asplit', n)
    acuts = [asplit.filter('aselect', f"gte(t,{start})*lt(t,{end})").filter("asetpts", "PTS-STARTPTS") for asplit, (start, end) in zip(asplits, scenes)]
    cuts = itertools.chain.from_iterable(zip(vcuts, acuts))
    out = (
        ffmpeg
        .concat(*cuts, n=n, v=1, a=1)
        .output(str(destination_path))
        .overwrite_output()
    )
    ffmpeg.run(out, capture_stdout=True, capture_stderr=True)


def extract_subtitles(video_path: Path, sub_path: Path, sub_index: int):
    input = ffmpeg.input(video_path)
    subtitles = input[f's:{sub_index}']
    out = ffmpeg.output(subtitles, str(sub_path)).overwrite_output()
    ffmpeg.run(out, capture_stdout=True, capture_stderr=True)


def add_subtitles(source_video: Path, source_subtitles: Path, destination_video: Path):
    input = ffmpeg.input(source_video)
    subtitles = ffmpeg.input(source_subtitles)['s']
    audio = input.audio
    video = input.video
    out = ffmpeg.output(video, audio, subtitles, str(destination_video), acodec='copy', vcodec='copy')
    ffmpeg.run(out)


def get_metadata(video_path: Path) -> VideoMetaData:
    probe = ffmpeg.probe(video_path)
    duration = float(probe["format"]["duration"])
    video_stream_count = audio_stream_count = subtitle_stream_count = 0
    for stream in probe["streams"]:
        kind = stream["codec_type"]
        if kind == "video":
            video_stream_count += 1
        elif kind == "audio":
            audio_stream_count += 1
        elif kind == "subtitle":
            subtitle_stream_count += 1
        else:
            print(f"Unknown stream type {kind}")
    return VideoMetaData(duration, video_stream_count, audio_stream_count, subtitle_stream_count)
