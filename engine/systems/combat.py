"""Combat system — resolve attacks, apply stealth penalties, handle destruction."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from ..core.enums import WeaponType
from ..core.events import AttackEvent, DestructionEvent, ExposureEvent

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


WEAPON_COSTS = {
    WeaponType.CONVENTIONAL: {'stealth_cost': 0.3, 'energy_cost': 30, 'cap': 0.88},
    WeaponType.PHOTOID: {'stealth_cost': 0.5, 'energy_cost': 50, 'cap': 0.88},
    WeaponType.DUAL_VECTOR_FOIL: {'stealth_cost': 0.9, 'energy_cost': 200, 'cap': 0.95},
}


def resolve_attack(
    attacker: Civilization,
    target: Civilization,
    universe: Universe,
    weapon: WeaponType = WeaponType.CONVENTIONAL,
) -> bool:
    """Resolve attack. Returns True if target destroyed.

    - Unlimited range if weapon is PHOTOID or DUAL_VECTOR_FOIL
    - Otherwise requires target within detection_range
    - Applies weapon-specific stealth/energy costs
    - Publishes AttackEvent, DestructionEvent (on success), ExposureEvent for attacker
    """
    costs = WEAPON_COSTS[weapon]

    # Range check (skip for photoid/dual_vector_foil)
    if weapon not in (WeaponType.PHOTOID, WeaponType.DUAL_VECTOR_FOIL):
        dist = attacker.position.distance_to(target.position, width=universe.width)
        if dist > attacker.military.detection_range:
            universe.log_event(
                f'{attacker.name} 尝试攻击 {target.name} 但目标超出探测范围'
            )
            return False

    # Apply costs
    apply_stealth_penalty(attacker, costs['stealth_cost'], universe, cause='attack')
    attacker.economy.energy = max(0.0, attacker.economy.energy - costs['energy_cost'])

    # Calculate success probability
    power_ratio = attacker.military.military_power / max(target.military.military_power, 1.0)
    base_prob = 0.35 * power_ratio
    success_prob = min(costs['cap'], base_prob)

    success = random.random() < success_prob

    universe.event_bus.publish(AttackEvent(
        turn=universe.turn,
        attacker_id=attacker.id,
        attacker_name=attacker.name,
        target_id=target.id,
        target_name=target.name,
        weapon=weapon,
        success=success,
        power_ratio=power_ratio,
        success_prob=success_prob,
    ))

    if success:
        target.is_destroyed = True
        target.destroyed_by = attacker.id
        attacker.kill_count += 1

        universe.event_bus.publish(DestructionEvent(
            turn=universe.turn,
            destroyed_id=target.id,
            destroyed_name=target.name,
            destroyed_by=attacker.id,
            weapon=weapon,
        ))
        universe.log_event(
            f'💥 {attacker.name} 使用{weapon.label}摧毁了 {target.name}！'
        )

        # Attacker is exposed by the attack
        universe.event_bus.publish(ExposureEvent(
            turn=universe.turn,
            civ_id=attacker.id,
            civ_name=attacker.name,
            cause='attack',
            stealth_old=attacker.military.stealth + costs['stealth_cost'],
            stealth_new=attacker.military.stealth,
        ))
    else:
        universe.log_event(
            f'{attacker.name} 攻击 {target.name} 失败 '
            f'(成功率: {success_prob:.2f})'
        )

    return success


def apply_stealth_penalty(
    civ: Civilization, amount: float, universe: Universe, cause: str = 'attack',
) -> None:
    """Reduce stealth and publish ExposureEvent."""
    old_stealth = civ.military.stealth
    civ.military.reduce_stealth(amount)
    new_stealth = civ.military.stealth

    universe.event_bus.publish(ExposureEvent(
        turn=universe.turn,
        civ_id=civ.id,
        civ_name=civ.name,
        cause=cause,
        stealth_old=old_stealth,
        stealth_new=new_stealth,
    ))
