"""Core layer — zero internal dependencies."""

from .coord import Coord
from .enums import Strategy, Action, TreatyType, CivState, WeaponType
from .events import EventBus, GameEvent, AttackEvent, BroadcastEvent, TreatyEvent, \
    BreakthroughEvent, DestructionEvent, DetectionEvent, DeterrenceEvent, \
    StrikeEvent, ExposureEvent, ArmsRaceEvent
from .state_machine import StateMachine, transition
