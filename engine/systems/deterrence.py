"""Deterrence system — declare deterrence, stability checks, collapse handling."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ..core.enums import CivState
from ..core.events import DeterrenceEvent

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


def declare_deterrence(
    declarer: Civilization, target: Civilization, universe: Universe,
) -> None:
    """Declarer: 'if you attack me, I broadcast your coordinates'.

    Both enter DETERRED state. Publishes DeterrenceEvent.
    """
    declarer.diplomacy.deterrence_declared = True
    declarer.diplomacy.deterrence_target = target.id

    try:
        declarer.state_machine.transition(CivState.DETERRED, 'deterrence_declared')
    except ValueError:
        pass
    try:
        target.state_machine.transition(CivState.DETERRED, 'deterrence_declared_on_us')
    except ValueError:
        pass

    universe.event_bus.publish(DeterrenceEvent(
        turn=universe.turn,
        declarer_id=declarer.id,
        declarer_name=declarer.name,
        target_id=target.id,
        target_name=target.name,
        action='declared',
    ))
    universe.log_event(
        f'{declarer.name} 对 {target.name} 发出威慑宣言'
    )


def check_deterrence_stability(
    declarer: Civilization, target: Civilization, universe: Universe,
) -> bool:
    """Check if deterrence holds.

    Based on: declarer.resolve, whether declarer actually has broadcast capability,
    target's perception of declarer's resolve.

    Returns True if stable, False if collapsing.
    """
    # Must have broadcast capability for deterrence to be credible
    if not declarer.military.has_broadcast_capability:
        return False

    # Declarer's resolve
    resolve_score = declarer.traits.resolve

    # Target's perception (paranoia makes them believe the threat more)
    belief = target.traits.paranoia

    # Stability score: resolve + belief must be high enough
    stability = (resolve_score + belief) / 2.0

    # Additional penalty if declarer is significantly weaker
    power_ratio = declarer.military.military_power / max(target.military.military_power, 1.0)
    if power_ratio < 0.5:
        stability -= 0.2

    return stability >= 0.4


def process_deterrence_collapse(
    civ: Civilization, target: Civilization, universe: Universe,
) -> None:
    """Deterrence fails -> target launches preemptive strike.

    State -> AT_WAR. Publishes DeterrenceEvent(action='broken').
    """
    try:
        civ.state_machine.transition(CivState.AT_WAR, 'deterrence_collapse')
    except ValueError:
        pass
    try:
        target.state_machine.transition(CivState.AT_WAR, 'deterrence_collapse')
    except ValueError:
        pass

    civ.diplomacy.deterrence_declared = False
    civ.diplomacy.deterrence_target = ''

    universe.event_bus.publish(DeterrenceEvent(
        turn=universe.turn,
        declarer_id=civ.id,
        declarer_name=civ.name,
        target_id=target.id,
        target_name=target.name,
        action='broken',
    ))
    universe.log_event(
        f'威慑崩溃：{civ.name} 对 {target.name} 的威慑失效！'
    )

    # Target launches preemptive strike
    from . import combat
    combat.resolve_attack(target, civ, universe)


def evaluate_counter_deterrence(
    civ: Civilization, deterrer: Civilization, universe: Universe,
) -> bool:
    """Can the target counter-deter?

    Requires: high resolve, high military.
    If succeed, both remain DETERRED.
    """
    resolve_score = civ.traits.resolve
    power_ratio = civ.military.military_power / max(deterrer.military.military_power, 1.0)

    # Need resolve > 0.6 and power_ratio > 0.7
    if resolve_score > 0.6 and power_ratio > 0.7:
        universe.event_bus.publish(DeterrenceEvent(
            turn=universe.turn,
            declarer_id=civ.id,
            declarer_name=civ.name,
            target_id=deterrer.id,
            target_name=deterrer.name,
            action='counter_declared',
        ))
        universe.log_event(
            f'{civ.name} 对 {deterrer.name} 发出反威慑！双方陷入恐怖平衡。'
        )
        return True
    return False
