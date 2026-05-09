"""Economy component — population, energy, and technology."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .military import MilitaryComponent


@dataclass
class EconomyComponent:
    """Manages a civilization's economic resources.

    All resource quantities are abstract and dimensionless.
    """

    population: float = 50.0
    energy: float = 300.0
    tech_level: float = 1.0

    def grow(self) -> None:
        """Increase population by a random 3-8, consuming 20 energy.

        Fails silently if energy is insufficient (population still grows
        but energy is clamped to 0).
        """
        self.population += random.uniform(3.0, 8.0)
        self.energy = max(0.0, self.energy - 20.0)

    def research(self, military: MilitaryComponent | None = None) -> None:
        """Advance technology by 4%, consuming 18 energy.

        If a MilitaryComponent is provided, also upgrades detection_range
        and military power as a side-effect (breakthrough synergy).

        Args:
            military: Optional military component to receive tech-upgrade side-effects.
        """
        self.tech_level *= 1.04
        self.energy = max(0.0, self.energy - 18.0)

        if military is not None:
            military.upgrade_from_research()

    def maintenance(self) -> None:
        """Deduct maintenance cost: energy -= population * 0.015."""
        self.energy = max(0.0, self.energy - self.population * 0.015)

    def can_afford(self, cost: float) -> bool:
        """Return True if the civilization has enough energy for *cost*."""
        return self.energy >= cost

    def to_dict(self) -> dict:
        """Serialize to plain dict."""
        return {
            'population': self.population,
            'energy': self.energy,
            'tech_level': self.tech_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> EconomyComponent:
        """Deserialize from dict."""
        return cls(
            population=data['population'],
            energy=data['energy'],
            tech_level=data['tech_level'],
        )
