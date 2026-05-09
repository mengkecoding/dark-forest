"""Cleaner strategy — hunt broadcasters with photoid strikes, never reveal self."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.enums import Action, WeaponType
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..civilization import Civilization


class CleanerStrategy(BaseStrategy):
    """The ultimate predator — cleanse the galaxy of those who make noise.

    - NEVER broadcast self, NEVER communicate, NEVER sign treaties.
    - Scan global broadcast signals first.
    - If a broadcast target is found → PHOTOID strike (100% response).
    - If target tech > cleaner tech * 2 → evaluate DUAL_VECTOR_FOIL (risk_taking).
    - If no broadcast signals → RESEARCH (improve weapons).
    """

    @property
    def label(self) -> str:
        return '清理者'

    def decide(self, civ: Civilization, universe) -> Action:
        # 1. Scan for active broadcasts
        broadcasts = self._get_broadcasts(universe)

        if broadcasts:
            for bc in broadcasts:
                target_id = bc.get('target_id', '')
                source_id = bc.get('broadcaster_id', '')

                # Determine strike target
                strike_id = target_id or source_id
                if not strike_id or strike_id == civ.id:
                    continue

                # Evaluate target tech level
                target_tech = self._get_tech(strike_id, universe)
                my_tech = civ.economy.tech_level

                if target_tech > my_tech * 2.0:
                    # Risky target — evaluate dual vector foil
                    if civ.traits.risk_taking > 0.6:
                        # Will use DUAL_VECTOR_FOIL (implicit in attack)
                        return Action.ATTACK
                    else:
                        # Too risky — skip, keep researching
                        continue

                # PHOTOID strike
                return Action.ATTACK

        # No broadcast signals → research
        return Action.RESEARCH

    def _get_broadcasts(self, universe) -> list[dict]:
        """Return list of active broadcast dicts from the universe."""
        if hasattr(universe, 'get_active_broadcasts'):
            return universe.get_active_broadcasts() or []
        return []

    def _get_tech(self, civ_id: str, universe) -> float:
        """Fetch tech_level of target civilization from the universe."""
        if hasattr(universe, 'civs') and civ_id in universe.civs:
            other = universe.civs[civ_id]
            if hasattr(other, 'economy'):
                return other.economy.tech_level
        return 1.0
