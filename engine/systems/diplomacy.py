"""Diplomacy system — communication, treaty proposals, treaty lifecycle."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.enums import TreatyType, CivState
from ..core.events import TreatyEvent, ExposureEvent

if TYPE_CHECKING:
    from ..civ.civilization import Civilization
    from ..universe import Universe


def process_communication(sender: Civilization, receiver: Civilization, universe: Universe) -> None:
    """Establish contact: both learn of each other. Sender exposes self more than receiver.

    Sender stealth reduces by 0.05, receiver by 0.02.
    """
    # Both learn of each other
    _learn_of(sender, receiver)
    _learn_of(receiver, sender)

    # Sender exposes self
    sender.military.reduce_stealth(0.05)
    receiver.military.reduce_stealth(0.02)

    sender.diplomacy.communication_log.append(
        f'T{turn(universe)}: 向 {receiver.name} 发送通信'
    )
    receiver.diplomacy.communication_log.append(
        f'T{turn(universe)}: 收到 {sender.name} 的通信'
    )

    universe.log_event(f'{sender.name} 向 {receiver.name} 发起通信')


def evaluate_treaty_response(
    proposer: Civilization, target: Civilization, treaty_type: TreatyType, universe: Universe,
) -> bool:
    """Target evaluates whether to accept treaty.

    Based on: trust(reputation * suspicion), military power ratio,
    proposer traits.aggression.
    """
    trust = target.diplomacy.evaluate_trust(
        proposer.diplomacy.reputation, target.traits.paranoia,
    )
    power_ratio = proposer.military.military_power / max(target.military.military_power, 1.0)

    # Aggression penalty
    aggression_penalty = proposer.traits.aggression * 0.3

    # Base acceptance threshold varies by treaty type
    thresholds = {
        TreatyType.NON_AGGRESSION: 0.25,
        TreatyType.TRADE: 0.4,
        TreatyType.ALLIANCE: 0.6,
    }
    threshold = thresholds.get(treaty_type, 0.5)

    # Lower threshold for weaker proposers (targets don't feel threatened)
    if power_ratio < 0.8:
        threshold -= 0.1
    elif power_ratio > 1.5:
        threshold += 0.15  # Fear of stronger civ

    score = trust - aggression_penalty
    return score >= threshold


def process_treaty_proposal(
    proposer: Civilization, target: Civilization, treaty_type: TreatyType, universe: Universe,
) -> None:
    """Propose treaty -> evaluate -> sign or reject. Publishes TreatyEvent."""
    universe.event_bus.publish(TreatyEvent(
        turn=universe.turn,
        civ_a=proposer.id,
        civ_b=target.id,
        treaty_type=treaty_type,
        action='proposed',
    ))

    accepted = evaluate_treaty_response(proposer, target, treaty_type, universe)

    if accepted:
        # Both sides sign
        proposer.diplomacy.propose_treaty(target.id, treaty_type)
        target.diplomacy.propose_treaty(proposer.id, treaty_type)

        proposer.diplomacy.communication_log.append(
            f'T{turn(universe)}: 与 {target.name} 签署 {treaty_type.value}'
        )
        target.diplomacy.communication_log.append(
            f'T{turn(universe)}: 与 {proposer.name} 签署 {treaty_type.value}'
        )

        universe.event_bus.publish(TreatyEvent(
            turn=universe.turn,
            civ_a=proposer.id,
            civ_b=target.id,
            treaty_type=treaty_type,
            action='signed',
        ))

        # Alliance -> transition to ALLIED state
        if treaty_type == TreatyType.ALLIANCE:
            try:
                proposer.state_machine.transition(CivState.ALLIED, 'alliance_signed')
            except ValueError:
                pass
            try:
                target.state_machine.transition(CivState.ALLIED, 'alliance_signed')
            except ValueError:
                pass

        universe.log_event(
            f'{proposer.name} 与 {target.name} 签署了 {treaty_type.value} 条约'
        )
    else:
        universe.event_bus.publish(TreatyEvent(
            turn=universe.turn,
            civ_a=proposer.id,
            civ_b=target.id,
            treaty_type=treaty_type,
            action='rejected',
        ))
        universe.log_event(
            f'{target.name} 拒绝了 {proposer.name} 的 {treaty_type.value} 条约'
        )


def process_break_treaty(civ: Civilization, target_id: str, universe: Universe) -> None:
    """Break treaty: reputation=0, broadcast betrayal to all known civs.

    Target's state changes (if allied->at_war). Publishes TreatyEvent, ExposureEvent.
    """
    target = _find_civ(target_id, universe)
    target_name = target.name if target else target_id

    # Find the treaty type before breaking
    treaty = civ.diplomacy.treaties.get(target_id)
    treaty_type = treaty.type if treaty else TreatyType.NON_AGGRESSION

    civ.diplomacy.break_treaty(target_id)

    if target:
        target.diplomacy.break_treaty(civ.id)
        if target.state_machine.current == CivState.ALLIED:
            try:
                target.state_machine.transition(CivState.AT_WAR, 'betrayed')
            except ValueError:
                pass

    # Notify all known civs of the betrayal
    for other in universe.civilizations:
        if other.id == civ.id or other.is_destroyed:
            continue
        if other.id in civ.memory.known_civs:
            other.diplomacy.communication_log.append(
                f'T{turn(universe)}: {civ.name} 背叛了 {target_name}'
            )

    universe.event_bus.publish(TreatyEvent(
        turn=universe.turn,
        civ_a=civ.id,
        civ_b=target_id,
        treaty_type=treaty_type,
        action='broken',
    ))
    universe.event_bus.publish(ExposureEvent(
        turn=universe.turn,
        civ_id=civ.id,
        civ_name=civ.name,
        cause='betrayal',
        stealth_old=civ.military.stealth,
        stealth_new=civ.military.stealth,
    ))
    universe.log_event(f'{civ.name} 撕毁了与 {target_name} 的条约！')


def tick_treaties(civ: Civilization, universe: Universe) -> None:
    """Decrement treaty turns. Expired treaties publish TreatyEvent(action='expired')."""
    expired_ids = [
        pid for pid, t in civ.diplomacy.treaties.items()
        if t.turns_remaining <= 1
    ]
    for pid in expired_ids:
        treaty = civ.diplomacy.treaties[pid]
        target = _find_civ(pid, universe)
        target_name = target.name if target else pid
        universe.event_bus.publish(TreatyEvent(
            turn=universe.turn,
            civ_a=civ.id,
            civ_b=pid,
            treaty_type=treaty.type,
            action='expired',
        ))
        universe.log_event(f'{civ.name} 与 {target_name} 的 {treaty.type.value} 条约到期')

        # Remove from both sides
        civ.diplomacy.treaties.pop(pid, None)
        if target:
            target.diplomacy.treaties.pop(civ.id, None)

    # Decrement remaining
    for t in list(civ.diplomacy.treaties.values()):
        t.turns_remaining -= 1


# ── helpers ──────────────────────────────────────────────────

def _learn_of(learner: Civilization, other: Civilization) -> None:
    """Add *other* to *learner*'s memory if not already known."""
    if other.id not in learner.memory.known_civs:
        learner.memory.add(other.id, {
            'name': other.name,
            'strategy': getattr(other.strategy, 'label', 'unknown'),
            'position': other.position.to_dict(),
            'military_power': other.military.military_power,
            'has_broadcast': other.military.has_broadcast_capability,
        })


def _find_civ(civ_id: str, universe: Universe) -> Civilization | None:
    """Find a civilization by id in the universe."""
    for c in universe.civilizations:
        if c.id == civ_id:
            return c
    return None


def turn(universe: Universe) -> int:
    return universe.turn
