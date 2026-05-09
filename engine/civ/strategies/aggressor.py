"""Aggressor strategy — attack the weak, arms-race peers, preempt threats."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ...core.enums import Action, CivState
from .base import BaseStrategy

if TYPE_CHECKING:
    from ..civilization import Civilization


class AggressorStrategy(BaseStrategy):
    """Dominate through military force.

    - Attack the weakest neighbor when power_ratio > 1.2.
    - If power_ratio in [0.8, 1.2] → ALERT state (arms race).
    - If no targets exist → research/expand.
    - Preventive strike: attack neighbors with low military but high tech growth.
    """

    @property
    def label(self) -> str:
        return '侵略者'

    def decide(self, civ: Civilization, universe) -> Action:
        targets = self._known_targets(civ, universe)
        my_power = civ.military.military_power

        if not targets:
            # No one to fight — invest
            if civ.economy.energy > 150:
                return Action.EXPAND
            return Action.RESEARCH

        # Sort targets by military_power ascending (weakest first)
        targets.sort(key=lambda t: t['military_power'])
        
        # Pick weakest target we haven't recently attacked
        recent_attacks = getattr(civ, '_recent_attack_targets', set())
        target = None
        for t in targets:
            if t['id'] not in recent_attacks:
                target = t
                break
        if target is None:
            # All targets recently attacked — cool down, research
            return Action.RESEARCH
            
        weakest = target
        power_ratio = my_power / max(weakest['military_power'], 1.0)

        # Preventive strike: low military but high tech growth → attack
        if weakest['military_power'] < my_power * 0.5:
            if weakest.get('tech_level', 1.0) > civ.economy.tech_level * 1.5:
                return Action.ATTACK

        if power_ratio > 1.2:
            return Action.ATTACK

        if 0.8 <= power_ratio <= 1.2:
            # Arms race — go to ALERT
            try:
                civ.state_machine.transition(CivState.ALERT, 'peer_detected')
            except ValueError:
                pass
            # Broadcast detection of peer to deter
            if civ.military.has_broadcast_capability:
                return Action.BROADCAST_TARGET
            return Action.RESEARCH

        # Weaker than target — research to catch up
        return Action.RESEARCH

    def _known_targets(self, civ: Civilization, universe) -> list[dict]:
        """Return list of known civs (dicts with id, military_power, tech_level)."""
        targets = []
        for cid, data in civ.memory.known_civs.items():
            targets.append({
                'id': cid,
                'military_power': data.get('military_power', 10),
                'tech_level': data.get('tech_level', 1.0),
            })
        # Also include civs detected this turn via universe
        if hasattr(universe, 'get_detected_this_turn'):
            for cid in universe.get_detected_this_turn(civ) or []:
                if cid not in {t['id'] for t in targets}:
                    other = universe.civs.get(cid) if hasattr(universe, 'civs') else None
                    if other:
                        targets.append({
                            'id': cid,
                            'military_power': getattr(other, 'military', None) and other.military.military_power or 10,
                            'tech_level': getattr(other, 'economy', None) and other.economy.tech_level or 1.0,
                        })
        return targets
