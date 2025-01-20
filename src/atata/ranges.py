from typing import List

from atata.structures import Range, Options


def prepare_ranges(
    ranges: List[Range], duration: float, options: Options
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
