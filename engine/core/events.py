"""Typed event system with publish-subscribe bus."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from .enums import TreatyType, WeaponType


# ── Base event ─────────────────────────────────────────────

@dataclass
class GameEvent:
    """Base class for all simulation events."""
    turn: int = 0

    @property
    def event_type(self) -> str:
        return type(self).__name__


# ── Concrete events ────────────────────────────────────────

@dataclass
class AttackEvent(GameEvent):
    attacker_id: str = ''
    attacker_name: str = ''
    target_id: str = ''
    target_name: str = ''
    weapon: WeaponType = WeaponType.CONVENTIONAL
    success: bool = False
    power_ratio: float = 0.0
    success_prob: float = 0.0


@dataclass
class BroadcastEvent(GameEvent):
    broadcaster_id: str = ''
    broadcaster_name: str = ''
    target_id: str = ''          # empty = self-broadcast
    target_name: str = ''
    is_self_broadcast: bool = True


@dataclass
class TreatyEvent(GameEvent):
    civ_a: str = ''
    civ_b: str = ''
    treaty_type: TreatyType = TreatyType.NON_AGGRESSION
    action: str = ''  # 'proposed' | 'signed' | 'broken' | 'expired'


@dataclass
class BreakthroughEvent(GameEvent):
    civ_id: str = ''
    civ_name: str = ''
    old_tech: float = 0.0
    new_tech: float = 0.0
    leaked: bool = False  # did nearby civs detect this?


@dataclass
class DestructionEvent(GameEvent):
    destroyed_id: str = ''
    destroyed_name: str = ''
    destroyed_by: str = ''
    weapon: WeaponType = WeaponType.CONVENTIONAL


@dataclass
class DetectionEvent(GameEvent):
    detector_id: str = ''
    detected_id: str = ''
    detection_type: str = ''  # 'passive' | 'active' | 'broadcast'


@dataclass
class DeterrenceEvent(GameEvent):
    declarer_id: str = ''
    declarer_name: str = ''
    target_id: str = ''
    target_name: str = ''
    action: str = ''  # 'declared' | 'broken' | 'counter_declared'


@dataclass
class StrikeEvent(GameEvent):
    """Third-party strike triggered by a broadcast signal."""
    striker_id: str = ''
    striker_name: str = ''
    target_id: str = ''
    target_name: str = ''
    weapon: WeaponType = WeaponType.PHOTOID
    broadcast_source_id: str = ''


@dataclass
class ExposureEvent(GameEvent):
    """A civilization's stealth was reduced due to external cause."""
    civ_id: str = ''
    civ_name: str = ''
    cause: str = ''  # 'attack' | 'breakthrough' | 'destruction_nearby'
    stealth_old: float = 0.0
    stealth_new: float = 0.0


@dataclass
class ArmsRaceEvent(GameEvent):
    civ_a: str = ''
    civ_b: str = ''
    military_a: float = 0.0
    military_b: float = 0.0


# ── Event bus ──────────────────────────────────────────────

Handler = Callable[[GameEvent], None]


class EventBus:
    """Simple publish-subscribe event bus.

    Systems subscribe to event types they care about.
    The runner publishes events after each action.

    Usage:
        bus = EventBus()
        bus.subscribe(AttackEvent, combat_system.on_attack)
        bus.publish(AttackEvent(turn=1, attacker_id='a', success=True))
    """

    def __init__(self) -> None:
        self._handlers: dict[str, list[Handler]] = {}
        self._history: list[GameEvent] = []

    def subscribe(self, event_type: type[GameEvent], handler: Handler) -> None:
        key = event_type.__name__
        if key not in self._handlers:
            self._handlers[key] = []
        self._handlers[key].append(handler)

    def publish(self, event: GameEvent) -> None:
        self._history.append(event)
        key = type(event).__name__
        for handler in self._handlers.get(key, []):
            handler(event)

    def history(self) -> list[GameEvent]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
