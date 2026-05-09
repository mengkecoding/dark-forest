"""Abstract base class for all civilization strategies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from ...core.enums import Action, Strategy as StrategyEnum

if TYPE_CHECKING:
    from ..civilization import Civilization


class BaseStrategy(ABC):
    """Every strategy must expose a label and implement decide().

    decide() inspects the civilization's internal state and the external
    universe to return the Action the civilization should take this turn.

    Strategies may also mutate the civilization (e.g. switching strategies)
    during decide().
    """

    @property
    @abstractmethod
    def label(self) -> str:
        """Human-readable name of this strategy."""
        ...

    @abstractmethod
    def decide(self, civ: Civilization, universe) -> Action:
        """Determine this turn's action.

        Args:
            civ: The civilization making the decision (may be mutated).
            universe: The simulation container (provides neighbor/broadcast info).

        Returns:
            The Action the civilization will execute this turn.
        """
        ...
