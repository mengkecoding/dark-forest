"""Economy system — maintenance, breakthrough checks."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ..core.events import BreakthroughEvent, ExposureEvent

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


def process_economy(civ: Civilization, universe: Universe) -> None:
    """Run civ.economy.maintenance(). If energy <= 0, civ enters crisis."""
    civ.economy.maintenance()

    if civ.economy.energy <= 0:
        universe.log_event(f'{civ.name} 能源耗尽，陷入危机！')
        # Crisis: population loss
        civ.economy.population = max(1.0, civ.economy.population * 0.9)


def process_breakthrough(civ: Civilization, universe: Universe) -> None:
    """Small chance (1-3% per turn, increasing with tech_level) of tech explosion.

    Tech *= 1.5-3.0. Publishes BreakthroughEvent.
    If tech jump > 2x, nearby civs may detect (leaked=True).
    """
    # Base chance 1.5%, increased by tech_level
    base_chance = 0.015
    tech_bonus = min(0.015, civ.economy.tech_level * 0.002)
    chance = base_chance + tech_bonus

    if random.random() >= chance:
        return

    # Breakthrough!
    magnitude = random.uniform(1.5, 3.0)
    old_tech = civ.economy.tech_level
    civ.economy.tech_level *= magnitude

    leaked = magnitude > 2.0

    universe.event_bus.publish(BreakthroughEvent(
        turn=universe.turn,
        civ_id=civ.id,
        civ_name=civ.name,
        old_tech=old_tech,
        new_tech=civ.economy.tech_level,
        leaked=leaked,
    ))
    universe.log_event(
        f'⚡ {civ.name} 取得科技突破！科技等级 {old_tech:.1f} -> {civ.economy.tech_level:.1f}'
    )

    if leaked:
        # Nearby civs may detect
        for other in universe.civilizations:
            if other.id == civ.id or other.is_destroyed:
                continue
            dist = other.position.distance_to(civ.position, width=universe.width)
            if dist <= other.military.detection_range * 1.5:
                if random.random() < 0.5:
                    if civ.id not in other.memory.known_civs:
                        other.memory.add(civ.id, {
                            'name': civ.name,
                            'strategy': getattr(civ.strategy, 'label', 'unknown'),
                            'position': civ.position.to_dict(),
                            'military_power': civ.military.military_power,
                            'has_broadcast': civ.military.has_broadcast_capability,
                        })
                        universe.event_bus.publish(ExposureEvent(
                            turn=universe.turn,
                            civ_id=civ.id,
                            civ_name=civ.name,
                            cause='breakthrough',
                            stealth_old=civ.military.stealth,
                            stealth_new=civ.military.stealth,
                        ))
                        universe.log_event(
                            f'{other.name} 探测到 {civ.name} 的技术突破能量信号！'
                        )
