import pathlib
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import ffmpeg, subtitles
from .options import Options, Range

BATCH_THRESHOLD = 5
MAX_INTERVAL_LENGTH = 30


@dataclass
class VideoMetaData:
    duration: float
    video_stream_count: int
    audio_stream_count: int
    subtitle_stream_count: int


def main():
    source_video = Path("s05e17.mkv")
    sub_index = 0
    audio_index = 1
    options = Options(BATCH_THRESHOLD, MAX_INTERVAL_LENGTH, create_prefix=True, create_suffix=True)

    suffix = get_suffix(options)
    destination_video = source_video.parent / f"{source_video.stem}{suffix}{source_video.suffix}"
    temp_dir = tempfile.TemporaryDirectory()
    temp_dir_path = pathlib.Path(temp_dir.name)
    initial_sub_path = temp_dir_path / "initial.srt"
    final_sub_path = temp_dir_path / "final.srt"
    temp_video = temp_dir_path / f"data{source_video.suffix}"

    metadata = ffmpeg.get_metadata(source_video)
    ffmpeg.extract_subtitles(source_video, initial_sub_path, sub_index)
    ranges = subtitles.process_subtitles(initial_sub_path, final_sub_path, options)
    scenes = prepare_ranges(ranges, metadata.duration, options)
    ffmpeg.cut_scenes(source_video, temp_video, scenes, audio_index)
    ffmpeg.add_subtitles(temp_video, final_sub_path, destination_video)


def prepare_ranges(ranges: Range, duration: float, options: options) -> Range:
    last_scene_end = 0
    rv = []
    for start, end in ranges:
        rv.append((last_scene_end, start))
        if options.create_prefix:
            rv.append((start, end))
        rv.append((start, end))
        if options.create_suffix:
            rv.append((start, end))
        last_scene_end = end
    rv.append((last_scene_end, duration))
    rv = compress_ranges(rv)
    return rv


def compress_ranges(ranges: Range) -> Range:
    rv = []
    prev = None
    for item in ranges:
        if prev is None:
            prev = item
            continue
        if prev[1] == item[0]:
            prev = (prev[0], item[1])
        else:
            rv.append(prev)
            prev = item
    rv.append(prev)
    return rv


def get_suffix(options: Options):
    a = "s" if options.create_prefix else ""
    b = "s" if options.create_suffix else ""
    return f".{a}t{b}"
