"""Civilization aggregate root — composes all sub-components and strategies."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from ..core.coord import Coord
from ..core.enums import Action
from ..core.state_machine import StateMachine

from .components.economy import EconomyComponent
from .components.military import MilitaryComponent
from .components.diplomacy import DiplomacyComponent
from .components.memory import MemoryComponent
from .traits import CivilizationTraits
from .strategies.base import BaseStrategy


@dataclass
class Civilization:
    """Top-level civilization object — the aggregate root.

    Holds all sub-components, traits, strategy, and immutable identity.
    The ``decide()`` method delegates to the active strategy and
    ``execute()`` applies the chosen action.

    Attributes:
        id: Short unique identifier (uuid4 hex[:8]).
        name: Human-readable display name.
        position: Current 2D coordinate in the universe.
        is_destroyed: Whether this civ has been eliminated.
        destroyed_by: Id of the civ that destroyed this one (empty if alive).
        kill_count: How many other civs this one has destroyed.
        turns_alive: Number of turns this civ has survived.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str = 'Unknown'
    position: Coord = field(default_factory=lambda: Coord(0, 0))
    is_destroyed: bool = False
    destroyed_by: str = ''
    kill_count: int = 0
    turns_alive: int = 0

    # Sub-components
    economy: EconomyComponent = field(default_factory=EconomyComponent)
    military: MilitaryComponent = field(default_factory=MilitaryComponent)
    diplomacy: DiplomacyComponent = field(default_factory=DiplomacyComponent)
    memory: MemoryComponent = field(default_factory=MemoryComponent)
    traits: CivilizationTraits = field(default_factory=CivilizationTraits)
    state_machine: StateMachine = field(default_factory=StateMachine)

    # Active strategy (mutable — can switch mid-simulation)
    strategy: BaseStrategy = field(default_factory=lambda: _default_strategy())

    def decide(self, universe) -> Action:
        """Ask the active strategy what to do this turn.

        Args:
            universe: The simulation container (provides neighbor/broadcast info).

        Returns:
            The Action the civilization should execute.
        """
        if self.is_destroyed:
            return Action.NOTHING
        return self.strategy.decide(self, universe)

    def execute(self, action: Action, universe) -> None:
        """Execute the chosen action against the universe.

        This method mutates the civilization's components and may publish
        events via the universe's EventBus.

        Args:
            action: The action to perform.
            universe: The simulation container.

        Note:
            This is a stub — the real execution logic will be implemented
            when the universe/combat systems are built.  For now it handles
            basic economic side-effects.
        """
        if self.is_destroyed:
            return

        self.turns_alive += 1

        if action == Action.RESEARCH:
            self.economy.research(self.military)
        elif action == Action.EXPAND:
            self.economy.grow()
        elif action == Action.ATTACK:
            self._execute_attack(universe)
        elif action == Action.BROADCAST_SELF:
            self.military.reduce_stealth(0.1)
        elif action == Action.BROADCAST_TARGET:
            self.military.reduce_stealth(0.05)
        elif action == Action.DETECT:
            self.economy.energy = max(0.0, self.economy.energy - 5.0)
        elif action == Action.COMMUNICATE:
            self.military.reduce_stealth(0.03)
        elif action == Action.PROPOSE_TREATY:
            self.economy.energy = max(0.0, self.economy.energy - 10.0)
        elif action == Action.DECLARE_DETERRENCE:
            self.diplomacy.deterrence_declared = True
            self.military.reduce_stealth(0.05)
        elif action == Action.BREAK_TREATY:
            # Handled by diplomacy component directly
            pass

        # Always run maintenance
        self.economy.maintenance()

        # Tick treaties
        self.diplomacy.tick_treaties()

    def to_dict(self) -> dict:
        """Serialize the entire civilization to a plain dict."""
        return {
            'id': self.id,
            'name': self.name,
            'strategy': self.strategy.label,
            'position': self.position.to_dict(),
            'is_destroyed': self.is_destroyed,
            'destroyed_by': self.destroyed_by,
            'kill_count': self.kill_count,
            'turns_alive': self.turns_alive,
            'has_broadcast': self.military.stealth < 0.1,
            'population': self.economy.population,
            'energy': self.economy.energy,
            'tech_level': self.economy.tech_level,
            'military_power': self.military.military_power,
            'stealth': self.military.stealth,
            'detection_range': self.military.detection_range,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Civilization:
        """Deserialize a civilization from a dict."""
        from ..core.coord import Coord
        return cls(
            id=data['id'],
            name=data['name'],
            position=Coord(**data['position']),
            is_destroyed=data.get('is_destroyed', False),
            destroyed_by=data.get('destroyed_by', ''),
            kill_count=data.get('kill_count', 0),
            turns_alive=data.get('turns_alive', 0),
            economy=EconomyComponent.from_dict(data['economy']),
            military=MilitaryComponent.from_dict(data['military']),
            diplomacy=DiplomacyComponent.from_dict(data['diplomacy']),
            memory=MemoryComponent.from_dict(data['memory']),
            traits=CivilizationTraits.from_dict(data['traits']),
            state_machine=_build_state_machine(data.get('state', 'peaceful')),
            strategy=_default_strategy(),
        )

    def _execute_attack(self, universe) -> None:
        """Stub for attack execution — full logic TBD in combat system."""
        self.economy.energy = max(0.0, self.economy.energy - 30.0)
        self.military.reduce_stealth(0.15)


def _default_strategy() -> BaseStrategy:
    """Return a default strategy (used for deserialization, overridden by factory)."""
    from .strategies.hider import HiderStrategy
    return HiderStrategy()


def _build_state_machine(state_value: str) -> StateMachine:
    """Build a StateMachine pre-set to the given state."""
    from ..core.enums import CivState
    sm = StateMachine()
    target = CivState(state_value)
    if sm.current != target:
        try:
            sm.transition(target, 'deserialized')
        except ValueError:
            # If transition isn't directly possible, start fresh
            sm = StateMachine(initial=target)
    return sm
