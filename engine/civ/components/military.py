"""Military component — power, stealth, detection, and weapon choice."""

from __future__ import annotations

from dataclasses import dataclass

from ...core.enums import WeaponType
from ..traits import CivilizationTraits


@dataclass
class MilitaryComponent:
    """Combat and sensing capabilities of a civilization.

    Attributes:
        military_power: Offensive/defensive strength (unbounded float).
        stealth: How hard the civ is to detect. Clamped [0.0, 1.0].
        detection_range: Passive scan radius in light-years. Clamped [10, 400].
        has_broadcast_capability: Whether the civ can emit broadcast signals.
    """

    military_power: float = 20.0
    stealth: float = 0.5
    detection_range: float = 50.0
    has_broadcast_capability: bool = True

    def __post_init__(self) -> None:
        """Clamp stealth and detection_range to their valid bounds."""
        self.stealth = max(0.0, min(1.0, self.stealth))
        self.detection_range = max(10.0, min(400.0, self.detection_range))

    def upgrade_from_research(self) -> None:
        """Apply research breakthrough: detection_range +8 (max 400), military *1.02."""
        self.detection_range = min(400.0, self.detection_range + 8.0)
        self.military_power *= 1.02

    def reduce_stealth(self, amount: float) -> None:
        """Reduce stealth by *amount*, floor at 0."""
        self.stealth = max(0.0, self.stealth - amount)

    def increase_stealth(self, amount: float) -> None:
        """Increase stealth by *amount*, ceiling at 1."""
        self.stealth = min(1.0, self.stealth + amount)

    def choose_weapon(
        self, target_tech: float, traits: CivilizationTraits,
    ) -> WeaponType:
        """Select the appropriate weapon type based on trait risk_taking and target tech.

        Rules:
        - If target_tech > self detection_range proxy → DUAL_VECTOR_FOIL (high risk)
        - If traits.risk_taking > 0.7 and target_tech > 3.0 → DUAL_VECTOR_FOIL
        - If traits.risk_taking > 0.4 or self.military_power > target_tech * 50 → PHOTOID
        - Otherwise → CONVENTIONAL
        """
        if target_tech > 8.0 and traits.risk_taking > 0.7:
            return WeaponType.DUAL_VECTOR_FOIL
        if traits.risk_taking > 0.4 or self.military_power > target_tech * 50:
            return WeaponType.PHOTOID
        return WeaponType.CONVENTIONAL

    def to_dict(self) -> dict:
        """Serialize to plain dict."""
        return {
            'military_power': self.military_power,
            'stealth': self.stealth,
            'detection_range': self.detection_range,
            'has_broadcast_capability': self.has_broadcast_capability,
        }

    @classmethod
    def from_dict(cls, data: dict) -> MilitaryComponent:
        """Deserialize from dict."""
        return cls(
            military_power=data['military_power'],
            stealth=data['stealth'],
            detection_range=data['detection_range'],
            has_broadcast_capability=data['has_broadcast_capability'],
        )
