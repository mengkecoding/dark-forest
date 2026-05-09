"""Observer strategy — watch silently, track everyone, share intel with allies."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.enums import Action
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..civilization import Civilization


class ObserverStrategy(BaseStrategy):
    """Passively observe the galaxy without revealing yourself.

    - DETECT silently, never broadcast.
    - Track all detected neighbors in detail.
    - Share intelligence with allies (via communication).
    - Focus on RESEARCH to improve detection range.
    """

    @property
    def label(self) -> str:
        return '观察者'

    def decide(self, civ: Civilization, universe) -> Action:
        # Never broadcast under any circumstance
        # Always detect first if we have energy
        if civ.economy.energy > 50:
            return Action.DETECT

        # Share intel with allies
        allies = self._get_allies(civ)
        if allies and civ.economy.energy > 30:
            return Action.COMMUNICATE

        # Default: research to improve detection
        return Action.RESEARCH

    def _get_allies(self, civ: Civilization) -> list[str]:
        """Return list of allied civilization ids."""
        allies = []
        for cid, treaty in civ.diplomacy.treaties.items():
            from ...core.enums import TreatyType
            if treaty.type in (TreatyType.ALLIANCE, TreatyType.NON_AGGRESSION):
                allies.append(cid)
        return allies
