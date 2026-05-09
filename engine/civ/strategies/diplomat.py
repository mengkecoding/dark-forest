"""Diplomat strategy — communicate, build trust, form alliances, deter threats."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ...core.enums import Action, TreatyType, CivState
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..civilization import Civilization


class DiplomatStrategy(BaseStrategy):
    """Build a web of trust and deterrence.

    - Communicate with newly detected neighbors.
    - Propose NON_AGGRESSION treaties with unaffiliated neighbors.
    - If treaty signed, later propose TRADE or ALLIANCE.
    - If reputation is high and neighbor threatens → DECLARE_DETERRENCE.
    - If betrayed → switch to HiderStrategy.
    """

    @property
    def label(self) -> str:
        return '外交家'

    def decide(self, civ: Civilization, universe) -> Action:
        # Check for betrayal
        if civ.state_machine.current == CivState.AT_WAR:
            # We are at war — switch to hider
            from .hider import HiderStrategy
            civ.strategy = HiderStrategy()
            return civ.strategy.decide(civ, universe)

        detected = self._new_detections(civ, universe)
        known = list(civ.memory.known_civs.keys())

        # 1. Communicate with newly detected neighbors
        if detected:
            return Action.COMMUNICATE

        # 2. Check for military threats FIRST — deterrence is urgent
        if civ.diplomacy.reputation > 0.4 and not civ.diplomacy.deterrence_declared:
            for cid, data in civ.memory.known_civs.items():
                mp = data.get('military_power', 0)
                if mp > civ.military.military_power * 1.3:
                    return Action.DECLARE_DETERRENCE

        # 3. Propose treaties with known neighbors
        for cid in known:
            treaty = civ.diplomacy.treaties.get(cid)
            if treaty is None:
                return Action.PROPOSE_TREATY
            # If we have non-aggression, consider upgrading
            if treaty.type == TreatyType.NON_AGGRESSION and treaty.turns_remaining < 40:
                return Action.PROPOSE_TREATY  # re-propose (sim will handle upgrade)
            if treaty.type == TreatyType.NON_AGGRESSION and treaty.turns_remaining > 35:
                # Propose trade or alliance
                if civ.economy.tech_level > 2.0:
                    # Propose trade
                    return Action.PROPOSE_TREATY
                else:
                    return Action.PROPOSE_TREATY  # alliance later

        # 4. Default — research
        return Action.RESEARCH

    def _new_detections(self, civ: Civilization, universe) -> bool:
        """True if new civs were detected this turn."""
        if hasattr(universe, 'get_detected_this_turn'):
            return bool(universe.get_detected_this_turn(civ))
        return False
