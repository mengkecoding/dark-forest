"""2D coordinate with distance and toroidal wrapping."""

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Coord:
    """Immutable 2D coordinate in the universe grid.

    All positions are in light-years.  The universe is toroidal (wrap-around).
    """

    x: float
    y: float

    def distance_to(self, other: 'Coord', width: float | None = None) -> float:
        """Euclidean distance, optionally accounting for toroidal wrap.

        Args:
            other: The target coordinate.
            width: If provided, the universe width for toroidal distance.
                   If None, plain Euclidean distance is used.

        Returns:
            Distance in light-years.
        """
        if width is None:
            return math.hypot(self.x - other.x, self.y - other.y)

        # Toroidal distance — shortest path across wrap boundaries
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        dx = min(dx, width - dx)
        dy = min(dy, width - dy)
        return math.hypot(dx, dy)

    def wrap(self, width: float) -> 'Coord':
        """Return a new Coord wrapped to [0, width)."""
        return Coord(self.x % width, self.y % width)

    def to_dict(self) -> dict:
        return {'x': self.x, 'y': self.y}
