"""Earth-observation context layers.

Production: precomputed Copernicus/APEx rasters for the Kyiv area, looked up per
report. Until those exist, NullEO answers "no context" so scoring still works.
"""

from typing import Protocol

from .models import LatLon


class EOContext(Protocol):
    def dense_urban(self, p: LatLon) -> bool: ...
    def damaged(self, p: LatLon) -> bool: ...


class NullEO:
    def dense_urban(self, p: LatLon) -> bool:
        return False

    def damaged(self, p: LatLon) -> bool:
        return False
