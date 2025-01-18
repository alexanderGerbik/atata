from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Options:
    batch_threshold: int
    max_interval_length: int
    create_prefix: bool = True
    create_suffix: bool = True


Range = List[Tuple[float, float]]
