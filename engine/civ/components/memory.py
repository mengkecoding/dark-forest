"""Memory component — persistent knowledge of other civilizations."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MemoryComponent:
    """Stores what this civilization knows about others.

    Each entry maps civ_id → {
        'name': str,
        'strategy': str,
        'position': dict,       # {'x': float, 'y': float}
        'military_power': float,
        'has_broadcast': bool,
    }
    """

    known_civs: dict[str, dict] = field(default_factory=dict)

    def add(self, civ_id: str, data: dict) -> None:
        """Add or update knowledge about a civilization.

        Args:
            civ_id: The known civilization's id.
            data: Dict with keys name, strategy, position, military_power, has_broadcast.
        """
        self.known_civs[civ_id] = dict(data)

    def remove(self, civ_id: str) -> None:
        """Forget a civilization (e.g. it was destroyed)."""
        self.known_civs.pop(civ_id, None)

    def to_dict(self) -> dict:
        """Serialize to plain dict."""
        return {
            'known_civs': dict(self.known_civs),
        }

    @classmethod
    def from_dict(cls, data: dict) -> MemoryComponent:
        """Deserialize from dict."""
        return cls(known_civs=dict(data.get('known_civs', {})))
