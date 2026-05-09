"""Hider strategy — avoid detection, research in silence, only fight when cornered."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.enums import Action
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..civilization import Civilization


class HiderStrategy(BaseStrategy):
    """Survive by staying invisible.

    - HIDE when any neighbor is sensed (within detection_range).
    - RESEARCH or EXPAND when the coast is clear.
    - If a tech breakthrough gives overwhelming military dominance,
      switch to AggressorStrategy.
    """

    @property
    def label(self) -> str:
        return '隐藏者'

    def decide(self, civ: Civilization, universe) -> Action:
        # Check if any known neighbors are nearby (within detection range)
        neighbors_nearby = self._sensed_neighbors(civ, universe)

        if neighbors_nearby:
            return Action.HIDE

        # Safe — invest in growth
        # Alternate between research and expansion based on energy
        if civ.economy.energy > 100 and civ.economy.population < 200:
            return Action.EXPAND

        # Tech-explosion check: if military is dominant, switch to aggressor
        if civ.military.military_power > 200 and civ.economy.tech_level > 5.0:
            from .aggressor import AggressorStrategy
            civ.strategy = AggressorStrategy()
            return civ.strategy.decide(civ, universe)

        return Action.RESEARCH

    def _sensed_neighbors(self, civ: Civilization, universe) -> bool:
        """Return True if any known civilization is within detection_range."""
        detection = civ.military.detection_range

        for cid, data in civ.memory.known_civs.items():
            pos_data = data.get('position', {})
            from ...core.coord import Coord
            neighbor_pos = Coord(pos_data.get('x', 0), pos_data.get('y', 0))
            dist = civ.position.distance_to(neighbor_pos)
            if dist <= detection:
                return True

        # Also check universe-level detection (detected this turn)
        if hasattr(universe, 'get_detected_this_turn'):
            detected = universe.get_detected_this_turn(civ)
            if detected:
                return True

        return False
