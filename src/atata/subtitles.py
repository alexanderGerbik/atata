import datetime
import itertools
from typing import List
from pathlib import Path

import pysrt
from pysrt import SubRipTime, SubRipItem

from .options import Options, Range


def process_subtitles(in_file: Path, options: Options) -> List[Range]:
    subs = pysrt.open(in_file)
    batches = _split_into_batches(subs, options)
    assert batches[-1][-1] == subs[-1]
    ranges = []
    for batch in batches:
        start = _to_seconds(batch[0].start)
        end = _to_seconds(batch[-1].end)
        ranges.append(Range(start, end, has_subtitle=True))
    return ranges


def _split_into_batches(subs: List[SubRipItem], options: Options) -> List[List[SubRipItem]]:
    batches = []
    current_batch = [subs[0]]
    for prev_sub, sub in itertools.pairwise(subs):
        if _get_difference(prev_sub, sub) < options.batch_threshold:
            current_batch.append(sub)
        else:
            batches.append(current_batch)
            current_batch = [sub]
    batches.append(current_batch)
    return list(itertools.chain.from_iterable(_justify(b, options.max_interval_length) for b in batches))


def _justify(intervals: List[SubRipItem], max_length: float) -> List[List[SubRipItem]]:
    # badness=(remaining space)**3
    # dp[i]=min(dp[j+1]+badness(i,j))
    n = len(intervals)
    badness = [[float('inf')] * n for _ in range(n)]

    for i in range(n):
        line_length = 0
        for j in range(i, n):
            line_length += _get_length(intervals[j]) + (
                _get_difference(intervals[j - 1], intervals[j]) if j > i else 0)  # Add space between words
            if line_length <= max_length:
                badness[i][j] = (max_length - line_length) ** 3
            else:
                break

    dp = [float('inf')] * (n + 1)
    dp[n] = 0  # Base case
    splits = [-1] * n
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            if badness[i][j] != float('inf') and dp[j + 1] + badness[i][j] < dp[i]:
                dp[i] = dp[j + 1] + badness[i][j]
                splits[i] = j + 1

    lines = []
    i = 0
    while i < n:
        lines.append(intervals[i:splits[i]])
        i = splits[i]
    return lines


def _get_length(prev: SubRipItem, next: SubRipItem = None) -> float:
    if next is None:
        next = prev
    if next.end < prev.start:
        return 0
    return _to_seconds(next.end - prev.start)


def _get_difference(prev: SubRipItem, next: SubRipItem) -> float:
    if next.start < prev.end:
        return 0
    return _to_seconds(next.start - prev.end)


def _to_seconds(sub_rip_time: SubRipTime) -> float:
    t = sub_rip_time.to_time()
    t = datetime.timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
    return t.total_seconds()
