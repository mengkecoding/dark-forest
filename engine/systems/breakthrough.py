"""Breakthrough system — preventive strike evaluation, reverse engineering."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


def check_preventive_strike(
    civ: Civilization, target: Civilization, universe: Universe,
) -> bool:
    """Should civ preemptively strike target?

    Criteria:
    - target.tech_growth_rate > civ * 1.5 AND
    - target.military < civ.military * 0.7
    """
    tech_ratio = target.economy.tech_level / max(civ.economy.tech_level, 0.1)
    military_ratio = target.military.military_power / max(civ.military.military_power, 0.1)

    return tech_ratio > 1.5 and military_ratio < 0.7


def apply_reverse_engineering(
    victor: Civilization, defeated: Civilization, universe: Universe,
) -> None:
    """Victor gains tech boost from destroyed enemy.

    victor tech += defeated tech * 0.1
    """
    bonus = defeated.economy.tech_level * 0.1
    victor.economy.tech_level += bonus
    universe.log_event(
        f'{victor.name} 从 {defeated.name} 的残骸中获得技术提升 '
        f'(+{bonus:.2f})'
    )
