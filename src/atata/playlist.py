from pathlib import Path
from typing import List
from xml.etree import ElementTree as ET

from .options import Range

file_caching_value = "300"


def generate_playlist(
    ranges: List[Range],
    video_path: Path,
    sub_path: Path,
    duration: float,
    playlist_path: Path,
):
    root = ET.Element(
        "playlist",
        {
            "xmlns": "http://xspf.org/ns/0/",
            "xmlns:vlc": "http://www.videolan.org/vlc/playlist/ns/0/",
            "version": "1",
        },
    )
    ET.SubElement(root, "title").text = "Playlist"
    track_list = ET.SubElement(root, "trackList")
    id_list = _generate_extension_element(root)
    for i, range in enumerate(ranges):
        track = ET.SubElement(track_list, "track")
        ET.SubElement(track, "location").text = f"file://{video_path}"
        ET.SubElement(track, "duration").text = str(int(duration))
        ET.SubElement(track, "annotation").text = _generate_anotation(range)
        params_element = _generate_extension_element(track)
        ET.SubElement(params_element, "vlc:id").text = str(i)
        _add_option(params_element, "file-caching", file_caching_value)
        _add_option(params_element, "start-time", _format_time(range.start))
        _add_option(params_element, "stop-time", _format_time(range.end))
        if range.has_subtitle:
            _add_option(params_element, "sub-file", str(sub_path))
        ET.SubElement(id_list, "vlc:item", {"tid": str(i)})
    _wrap(root)
    document = ET.ElementTree(root)
    document.write(playlist_path, "utf-8", True)


def _wrap(element, level=0):
    if not element.text:
        element.text = "\n" + "  " * (level + 1)
    element.tail = "\n" + "  " * level
    for child in element:
        _wrap(child, level + 1)


def _format_time(seconds: float):
    return f"{seconds:.3f}"


def _generate_anotation(range):
    start = _humanize(range.start)
    end = _humanize(range.end)
    sub = "T" if range.has_subtitle else "A"
    return f"{sub} {start}-{end}"


def _humanize(time: float) -> str:
    time = int(time)
    minutes, seconds = divmod(time, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"


def _add_option(parent_element, key, value):
    ET.SubElement(parent_element, "vlc:option").text = f"{key}={value}"


def _generate_extension_element(parent):
    return ET.SubElement(
        parent, "extension", {"application": "http://www.videolan.org/vlc/playlist/0"}
    )
