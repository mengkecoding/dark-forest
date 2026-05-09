"""Broadcast strike system — broadcast target coords, global strike response."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ..core.enums import WeaponType, Strategy as StrategyEnum
from ..core.events import BroadcastEvent, StrikeEvent, ExposureEvent, DetectionEvent

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


def broadcast_target_coords(
    broadcaster: Civilization, target: Civilization, universe: Universe,
) -> None:
    """Broadcast another civ's coordinates to entire universe.

    Broadcaster: stealth *= 0.5, energy -= 40.
    All civs in universe immediately learn target's position (add to memory).
    Publishes BroadcastEvent(is_self_broadcast=False).
    """
    # Costs
    broadcaster.military.reduce_stealth(broadcaster.military.stealth * 0.5)
    broadcaster.economy.energy = max(0.0, broadcaster.economy.energy - 40)

    # All civs learn target's position
    for civ in universe.civilizations:
        if civ.id == target.id or civ.is_destroyed:
            continue
        if target.id not in civ.memory.known_civs:
            civ.memory.add(target.id, {
                'name': target.name,
                'strategy': getattr(target.strategy, 'label', 'unknown'),
                'position': target.position.to_dict(),
                'military_power': target.military.military_power,
                'has_broadcast': target.military.has_broadcast_capability,
            })
            universe.event_bus.publish(DetectionEvent(
                turn=universe.turn,
                detector_id=civ.id,
                detected_id=target.id,
                detection_type='broadcast',
            ))

    universe.event_bus.publish(BroadcastEvent(
        turn=universe.turn,
        broadcaster_id=broadcaster.id,
        broadcaster_name=broadcaster.name,
        target_id=target.id,
        target_name=target.name,
        is_self_broadcast=False,
    ))
    universe.event_bus.publish(ExposureEvent(
        turn=universe.turn,
        civ_id=broadcaster.id,
        civ_name=broadcaster.name,
        cause='broadcast',
        stealth_old=broadcaster.military.stealth * 2,
        stealth_new=broadcaster.military.stealth,
    ))
    universe.log_event(
        f'{broadcaster.name} 向全宇宙广播了 {target.name} 的坐标！'
    )

    # Queue broadcast for strike processing
    universe.broadcast_signals.append({
        'broadcaster_id': broadcaster.id,
        'broadcaster_name': broadcaster.name,
        'target_id': target.id,
        'target_name': target.name,
        'turn': universe.turn,
    })


def process_global_strikes(target: Civilization, universe: Universe) -> None:
    """After a broadcast, check which civs want to strike.

    CLEANER: always strike (100%)
    Others: strike if traits.strike_response > random() threshold
    Multiple strikers may respond — first one wins.
    Uses PHOTOID by default, DUAL_VECTOR_FOIL for high-tech targets.
    Publishes StrikeEvent for each attempted strike.
    """
    from . import combat

    if target.is_destroyed:
        return

    strikers: list[Civilization] = []

    for civ in universe.civilizations:
        if civ.id == target.id or civ.is_destroyed:
            continue
        if civ.memory.known_civs.get(target.id) is None:
            continue

        strategy_label = getattr(civ.strategy, 'label', '')

        # CLEANER always strikes
        if strategy_label == '清理者':
            strikers.append(civ)
            continue

        # Others: based on strike_response trait
        threshold = 1.0 - civ.traits.strike_response
        if random.random() > threshold:
            strikers.append(civ)

    if not strikers:
        return

    # Sort by military power (strongest first)
    strikers.sort(key=lambda c: c.military.military_power, reverse=True)

    for striker in strikers:
        if target.is_destroyed:
            break

        # Choose weapon
        weapon = WeaponType.PHOTOID
        if target.economy.tech_level > 8.0 and striker.traits.risk_taking > 0.6:
            weapon = WeaponType.DUAL_VECTOR_FOIL

        universe.event_bus.publish(StrikeEvent(
            turn=universe.turn,
            striker_id=striker.id,
            striker_name=striker.name,
            target_id=target.id,
            target_name=target.name,
            weapon=weapon,
            broadcast_source_id='',
        ))
        universe.log_event(
            f'{striker.name} 响应广播，对 {target.name} 发起{weapon.label}打击'
        )

        success = combat.resolve_attack(striker, target, universe, weapon=weapon)
        if success:
            break  # First striker wins
