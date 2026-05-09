"""Chain exposure system — post-attack detection propagation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.events import ExposureEvent, DetectionEvent

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


def on_attack_exposed(attacker: Civilization, universe: Universe) -> None:
    """After an attack: nearby civs (within detection_range*2) may detect the attacker.

    Publishes ExposureEvent for each detection.
    """
    detection_radius = attacker.military.detection_range * 2

    for civ in universe.civilizations:
        if civ.id == attacker.id or civ.is_destroyed:
            continue
        dist = civ.position.distance_to(attacker.position, width=universe.width)
        if dist <= detection_radius:
            # 70% chance of detecting attacker
            import random
            if random.random() < 0.7:
                if attacker.id not in civ.memory.known_civs:
                    civ.memory.add(attacker.id, {
                        'name': attacker.name,
                        'strategy': getattr(attacker.strategy, 'label', 'unknown'),
                        'position': attacker.position.to_dict(),
                        'military_power': attacker.military.military_power,
                        'has_broadcast': attacker.military.has_broadcast_capability,
                    })
                    universe.event_bus.publish(ExposureEvent(
                        turn=universe.turn,
                        civ_id=attacker.id,
                        civ_name=attacker.name,
                        cause='attack_nearby',
                        stealth_old=attacker.military.stealth,
                        stealth_new=attacker.military.stealth,
                    ))
                    universe.log_event(
                        f'{civ.name} 通过攻击波动探测到 {attacker.name}'
                    )


def on_destruction_exposed(
    destroyed_civ: Civilization, attacker_name: str, universe: Universe,
) -> None:
    """When a civ is destroyed: all civs within range*3 get a detection event.

    The attacker's name is known to nearby civs.
    """
    destruction_radius = 50.0 * 3  # base detection * 3

    for civ in universe.civilizations:
        if civ.is_destroyed:
            continue
        dist = civ.position.distance_to(destroyed_civ.position, width=universe.width)
        if dist <= destruction_radius:
            # Check if attacker is known via detection
            for attacker_cand in universe.civilizations:
                if attacker_cand.name == attacker_name and not attacker_cand.is_destroyed:
                    if attacker_cand.id not in civ.memory.known_civs:
                        civ.memory.add(attacker_cand.id, {
                            'name': attacker_cand.name,
                            'strategy': getattr(attacker_cand.strategy, 'label', 'unknown'),
                            'position': attacker_cand.position.to_dict(),
                            'military_power': attacker_cand.military.military_power,
                            'has_broadcast': attacker_cand.military.has_broadcast_capability,
                        })
                        universe.log_event(
                            f'{civ.name} 观察到 {destroyed_civ.name} 被 {attacker_name} 摧毁的痕迹'
                        )
                    break


def propagate_exposure(civ: Civilization, universe: Universe) -> None:
    """Check if reduction in stealth causes neighbors to detect this civ."""
    for other in universe.civilizations:
        if other.id == civ.id or other.is_destroyed:
            continue
        dist = other.position.distance_to(civ.position, width=universe.width)
        if dist <= other.military.detection_range:
            # Detection chance based on civ's current stealth
            import random
            detect_chance = 1.0 - civ.military.stealth * 0.6
            if random.random() < detect_chance:
                if civ.id not in other.memory.known_civs:
                    other.memory.add(civ.id, {
                        'name': civ.name,
                        'strategy': getattr(civ.strategy, 'label', 'unknown'),
                        'position': civ.position.to_dict(),
                        'military_power': civ.military.military_power,
                        'has_broadcast': civ.military.has_broadcast_capability,
                    })
                    universe.event_bus.publish(DetectionEvent(
                        turn=universe.turn,
                        detector_id=other.id,
                        detected_id=civ.id,
                        detection_type='passive',
                    ))
                    universe.log_event(
                        f'{other.name} 因 {civ.name} 的暴露而探测到其存在'
                    )
