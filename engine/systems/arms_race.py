"""Arms race system — mutual detection, military buildup, cold peace evaluation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.enums import CivState
from ..core.events import ArmsRaceEvent

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


def check_mutual_detection(
    civ_a: Civilization, civ_b: Civilization, universe: Universe,
) -> None:
    """If both civs have each other in memory -> trigger ALERT state for both."""
    if civ_a.id in civ_b.memory.known_civs and civ_b.id in civ_a.memory.known_civs:
        try:
            civ_a.state_machine.transition(CivState.ALERT, 'mutual_detection')
        except ValueError:
            pass
        try:
            civ_b.state_machine.transition(CivState.ALERT, 'mutual_detection')
        except ValueError:
            pass

        universe.event_bus.publish(ArmsRaceEvent(
            turn=universe.turn,
            civ_a=civ_a.id,
            civ_b=civ_b.id,
            military_a=civ_a.military.military_power,
            military_b=civ_b.military.military_power,
        ))
        universe.log_event(
            f'{civ_a.name} 与 {civ_b.name} 互相发现，进入戒备状态'
        )


def process_arms_race(civ: Civilization, universe: Universe) -> None:
    """If in ALERT state: consume extra energy (15/turn) for military buildup.

    military *= 1.01 per turn. If energy depleted, force decision: attack or retreat.
    """
    if civ.state_machine.current != CivState.ALERT:
        return

    civ.economy.energy = max(0.0, civ.economy.energy - 15)
    civ.military.military_power *= 1.01

    if civ.economy.energy <= 0:
        _force_decision(civ, universe)


def evaluate_cold_peace(civ_a: Civilization, civ_b: Civilization) -> bool:
    """Cold peace holds if military power ratio is 0.8-1.2 AND neither attacks."""
    if civ_a.military.military_power <= 0 or civ_b.military.military_power <= 0:
        return False
    ratio = civ_a.military.military_power / civ_b.military.military_power
    return 0.8 <= ratio <= 1.2


# ── helpers ──────────────────────────────────────────────────

def _force_decision(civ: Civilization, universe: Universe) -> None:
    """Energy depleted during arms race — force attack on weakest known or retreat."""
    known_enemies = [
        (cid, data) for cid, data in civ.memory.known_civs.items()
    ]
    if not known_enemies:
        # Retreat — go back to PEACEFUL
        try:
            civ.state_machine.transition(CivState.PEACEFUL, 'threat_removed')
        except ValueError:
            pass
        universe.log_event(f'{civ.name} 能源耗尽，被迫撤退')
        return

    # Sort by military power ascending
    known_enemies.sort(key=lambda x: x[1].get('military_power', 0))
    weakest_id = known_enemies[0][0]

    target = None
    for c in universe.civilizations:
        if c.id == weakest_id and not c.is_destroyed:
            target = c
            break

    if target:
        from . import combat
        universe.log_event(f'{civ.name} 能源耗尽，被迫攻击 {target.name}')
        combat.resolve_attack(civ, target, universe)
    else:
        try:
            civ.state_machine.transition(CivState.PEACEFUL, 'threat_removed')
        except ValueError:
            pass
