from dataclasses import dataclass


@dataclass
class Options:
    batch_threshold: int
    max_interval_length: int
    create_prefix: bool = True
    create_suffix: bool = True


@dataclass
class Range:
    start: float
    end: float
    has_subtitle: bool = False


@dataclass
class VideoMetaData:
    duration: float
    video_stream_count: int
    audio_stream_count: int
    subtitle_stream_count: int
