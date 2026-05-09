"""Civilization state machine with transition rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .enums import CivState


@dataclass(frozen=True, slots=True)
class StateTransition:
    """A valid transition from one state to another, with optional condition."""
    from_state: CivState
    to_state: CivState
    label: str = ''

    def __repr__(self) -> str:
        return f'{self.from_state.value} --{self.label}--> {self.to_state.value}'


# ── Transition table ───────────────────────────────────────

TRANSITIONS: dict[CivState, list[StateTransition]] = {
    CivState.PEACEFUL: [
        StateTransition(CivState.PEACEFUL, CivState.ALERT, 'mutual_detection'),
        StateTransition(CivState.PEACEFUL, CivState.DETERRED, 'deterrence_declared_on_us'),
        StateTransition(CivState.PEACEFUL, CivState.AT_WAR, 'attacked'),
        StateTransition(CivState.PEACEFUL, CivState.ALLIED, 'alliance_signed'),
    ],
    CivState.ALERT: [
        StateTransition(CivState.ALERT, CivState.AT_WAR, 'attack_or_attacked'),
        StateTransition(CivState.ALERT, CivState.DETERRED, 'deterrence_declared'),
        StateTransition(CivState.ALERT, CivState.PEACEFUL, 'threat_removed'),
    ],
    CivState.DETERRED: [
        StateTransition(CivState.DETERRED, CivState.AT_WAR, 'deterrence_collapse'),
        StateTransition(CivState.DETERRED, CivState.ALLIED, 'trust_built'),
    ],
    CivState.AT_WAR: [
        StateTransition(CivState.AT_WAR, CivState.PEACEFUL, 'enemy_destroyed'),
        StateTransition(CivState.AT_WAR, CivState.DETERRED, 'mutual_deterrence'),
    ],
    CivState.ALLIED: [
        StateTransition(CivState.ALLIED, CivState.AT_WAR, 'betrayed'),
    ],
}


class StateMachine:
    """Manages a civilization's diplomatic/military state.

    Every state transition is validated against the transition table.
    Invalid transitions raise ValueError.
    """

    def __init__(self, initial: CivState = CivState.PEACEFUL) -> None:
        self._state = initial
        self._history: list[CivState] = [initial]

    @property
    def current(self) -> CivState:
        return self._state

    @property
    def history(self) -> list[CivState]:
        return list(self._history)

    def can_transition(self, to: CivState) -> bool:
        """Check if a transition from current state to *to* is valid."""
        valid_targets = {t.to_state for t in TRANSITIONS.get(self._state, [])}
        return to in valid_targets

    def transition(self, to: CivState, reason: str = '') -> None:
        """Attempt a state transition.

        Args:
            to: Target state.
            reason: Human-readable reason for the transition (for debugging).

        Raises:
            ValueError: If the transition is not allowed.
        """
        if to == self._state:
            return

        valid = {t.to_state: t for t in TRANSITIONS.get(self._state, [])}
        if to not in valid:
            allowed = ', '.join(valid.keys()) if valid else 'none'
            raise ValueError(
                f'Invalid transition: {self._state.value} -> {to.value}. '
                f'Allowed: {allowed}'
            )

        self._state = to
        self._history.append(to)


# Backward-compatible alias
def transition(machine: StateMachine, to: CivState, reason: str = '') -> None:
    machine.transition(to, reason)
