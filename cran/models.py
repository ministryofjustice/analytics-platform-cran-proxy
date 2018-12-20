from dataclasses import dataclass
from enum import IntEnum
from pathlib import Path

from urlobject import URLObject

Status = IntEnum("Status", "UNSEEN TOBUILD BUILDING NONBINARY FAILED BUILT")


@dataclass
class Package:
    url: URLObject
    fs_path: Path = None
    version: str = None
    name: str = None
    status: Status = Status.UNSEEN

    @property
    def filename(self):
        return self.url.path.segments[-1]

    def __hash__(self):
        return hash(self.url)
