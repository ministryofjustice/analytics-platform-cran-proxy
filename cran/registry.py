from typing import Set
from dataclasses import dataclass, field

from cran.models import Package


@dataclass
class Registry:
    packages: Set[Package] = field(default_factory=set)

    def get_by_url(self, url) -> Package:
        for package in self.packages:
            if package.url == url:
                return package

    def get_or_create(self, url):
        package = self.get_by_url(url)
        if not package:
            package = Package(url=url)
            self.packages.add(package)
        return package
