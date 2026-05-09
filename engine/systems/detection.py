"""Detection system — passive scanning, probabilistic detection, broadcast discovery."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


def detect_neighbors(civ: Civilization, universe: Universe) -> list[Civilization]:
    """Return neighbors within civ.military.detection_range using toroidal distance.

    A neighbor is another non-destroyed civilization whose position
    (via toroidal distance on universe.width) falls within the
    observer's detection_range.
    """
    results: list[Civilization] = []
    for other in universe.civilizations:
        if other.id == civ.id or other.is_destroyed:
            continue
        dist = civ.position.distance_to(other.position, width=universe.width)
        if dist <= civ.military.detection_range:
            results.append(other)
    return results


def try_detect_target(civ: Civilization, target: Civilization, universe: Universe) -> bool:
    """Probabilistic detection of a single target.

    success_chance = 1.0 - target.military.stealth * 0.6
    Returns True if detection succeeds.
    """
    # Already in memory → auto-detect (position known)
    if target.id in civ.memory.known_civs:
        return True

    chance = 1.0 - target.military.stealth * 0.6
    return random.random() < chance


def process_detection(civ: Civilization, universe: Universe) -> None:
    """Civ scans for neighbors, adds newly detected ones to civ.memory.known_civs.

    Publishes DetectionEvent for each new detection.
    """
    from ..core.events import DetectionEvent

    neighbors = detect_neighbors(civ, universe)
    for neighbor in neighbors:
        detected = try_detect_target(civ, neighbor, universe)
        if detected:
            old_entry = civ.memory.known_civs.get(neighbor.id)
            strategy_label = getattr(neighbor.strategy, 'label', 'unknown')
            civ.memory.add(neighbor.id, {
                'name': neighbor.name,
                'strategy': strategy_label,
                'position': neighbor.position.to_dict(),
                'military_power': neighbor.military.military_power,
                'has_broadcast': neighbor.military.has_broadcast_capability,
            })
            if old_entry is None:
                # New detection
                universe.event_bus.publish(DetectionEvent(
                    turn=universe.turn,
                    detector_id=civ.id,
                    detected_id=neighbor.id,
                    detection_type='passive',
                ))
                universe.log_event(
                    f'{civ.name} 探测到 {neighbor.name} '
                    f'(距离: {civ.position.distance_to(neighbor.position, width=universe.width):.1f}光年)'
                )


def detect_broadcasts(civ: Civilization, universe: Universe) -> None:
    """All broadcasters (stealth < 0.1 or has_broadcast=True with stealth < 0.1)
    are globally visible to everyone.

    A civ that has broadcasted its own position is detectable globally.
    """
    from ..core.events import DetectionEvent

    for other in universe.civilizations:
        if other.id == civ.id or other.is_destroyed:
            continue
        # A broadcaster is globally visible if stealth is very low due to broadcast
        if other.military.stealth < 0.1 and other.military.has_broadcast_capability:
            if other.id not in civ.memory.known_civs:
                civ.memory.add(other.id, {
                    'name': other.name,
                    'strategy': getattr(other.strategy, 'label', 'unknown'),
                    'position': other.position.to_dict(),
                    'military_power': other.military.military_power,
                    'has_broadcast': True,
                })
                universe.event_bus.publish(DetectionEvent(
                    turn=universe.turn,
                    detector_id=civ.id,
                    detected_id=other.id,
                    detection_type='broadcast',
                ))
                universe.log_event(
                    f'{civ.name} 接收到 {other.name} 的广播信号（全局可见）'
                )
