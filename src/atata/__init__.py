from dataclasses import dataclass
from pathlib import Path
from typing import List

from . import ffmpeg, subtitles
from .options import Options, Range
from .playlist import generate_playlist

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
    options = Options(
        BATCH_THRESHOLD, MAX_INTERVAL_LENGTH, create_prefix=True, create_suffix=True
    )

    source_video = source_video.resolve()
    suffix = get_suffix(options)
    sub_path = source_video.parent / f"{source_video.stem}{suffix}.srt"
    playlist_path = source_video.parent / f"{source_video.stem}{suffix}.xspf"

    metadata = ffmpeg.get_metadata(source_video)
    ffmpeg.extract_subtitles(source_video, sub_path, sub_index)
    ranges = subtitles.process_subtitles(sub_path, options)
    ranges = prepare_ranges(ranges, metadata.duration, options)
    generate_playlist(ranges, source_video, sub_path, metadata.duration, playlist_path)


def prepare_ranges(
    ranges: List[Range], duration: float, options: options
) -> List[Range]:
    last_scene_end = 0
    rv = []
    for item in ranges:
        rv.append(Range(last_scene_end, item.start))
        if options.create_prefix:
            rv.append(Range(item.start, item.end))
        rv.append(Range(item.start, item.end, has_subtitle=True))
        if options.create_suffix:
            rv.append(Range(item.start, item.end))
        last_scene_end = item.end
    rv.append(Range(last_scene_end, duration))
    rv = compress_ranges(rv)
    return rv


def compress_ranges(ranges: List[Range]) -> List[Range]:
    rv = []
    prev = None
    for item in ranges:
        if prev is None:
            prev = item
            continue
        if prev.end == item.start and prev.has_subtitle == item.has_subtitle:
            prev = Range(prev.start, item.end, item.has_subtitle)
        else:
            rv.append(prev)
            prev = item
    rv.append(prev)
    return rv


def get_suffix(options: Options):
    a = "a" if options.create_prefix else ""
    b = "a" if options.create_suffix else ""
    return f".{a}t{b}"
