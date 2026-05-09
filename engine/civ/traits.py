"""Civilization personality traits — seven float dimensions (0.0–1.0)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CivilizationTraits:
    """Seven personality dimensions that drive strategic decision-making.

    All values are clamped to [0.0, 1.0].
    """

    aggression: float = 0.5
    honor: float = 0.5
    resolve: float = 0.5
    risk_taking: float = 0.5
    expansionism: float = 0.5
    paranoia: float = 0.5
    strike_response: float = 0.5

    def __post_init__(self) -> None:
        """Clamp all trait values to [0.0, 1.0]."""
        for field_name in (
            'aggression', 'honor', 'resolve',
            'risk_taking', 'expansionism', 'paranoia', 'strike_response',
        ):
            val = getattr(self, field_name)
            setattr(self, field_name, max(0.0, min(1.0, val)))

    def to_dict(self) -> dict:
        """Serialize traits to a plain dict."""
        return {
            'aggression': self.aggression,
            'honor': self.honor,
            'resolve': self.resolve,
            'risk_taking': self.risk_taking,
            'expansionism': self.expansionism,
            'paranoia': self.paranoia,
            'strike_response': self.strike_response,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CivilizationTraits:
        """Deserialize traits from a dict."""
        return cls(**{k: data[k] for k in (
            'aggression', 'honor', 'resolve',
            'risk_taking', 'expansionism', 'paranoia', 'strike_response',
        )})
