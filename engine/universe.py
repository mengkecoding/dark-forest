"""Universe — the simulation container holding all civilizations and state."""

from __future__ import annotations

from dataclasses import dataclass, field

from .core.events import EventBus
from .civ.civilization import Civilization


@dataclass
class Universe:
    """The container for the entire dark forest simulation.

    Attributes:
        width: Toroidal universe width in light-years.
        civilizations: All active civilizations (destroyed ones included for history).
        turn: Current simulation turn (0-indexed).
        event_bus: Publish-subscribe bus for cross-system communication.
        broadcast_signals: Pending broadcast targets from this turn.
        event_log: Human-readable log entries (Chinese).
    """

    width: float = 500.0
    civilizations: list[Civilization] = field(default_factory=list)
    turn: int = 0
    event_bus: EventBus = field(default_factory=EventBus)
    broadcast_signals: list[dict] = field(default_factory=list)
    event_log: list[str] = field(default_factory=list)

    def get_neighbors(self, civ: Civilization, range_ly: float) -> list[Civilization]:
        """Return all non-destroyed neighbors within *range_ly* using toroidal distance."""
        results: list[Civilization] = []
        for other in self.civilizations:
            if other.id == civ.id or other.is_destroyed:
                continue
            dist = civ.position.distance_to(other.position, width=self.width)
            if dist <= range_ly:
                results.append(other)
        return results

    def log_event(self, msg: str) -> None:
        """Append a human-readable log entry."""
        self.event_log.append(f'[T{self.turn:04d}] {msg}')

    def get_detected_this_turn(self, civ: Civilization) -> list[str]:
        """Return ids of civs detected by *civ* this turn (via DetectionEvents)."""
        detected: list[str] = []
        for evt in self.event_bus.history():
            from .core.events import DetectionEvent
            if isinstance(evt, DetectionEvent) and evt.turn == self.turn:
                if evt.detector_id == civ.id:
                    detected.append(evt.detected_id)
        return detected

    def get_active_broadcasts(self) -> list[dict]:
        """Return list of active broadcast signals this turn."""
        return self.broadcast_signals

    def to_dict(self) -> dict:
        """Serialize the entire universe state to a plain dict."""
        return {
            'width': self.width,
            'turn': self.turn,
            'civilizations': [c.to_dict() for c in self.civilizations],
            'event_log': list(self.event_log),
            'broadcast_signals': list(self.broadcast_signals),
        }

    @classmethod
    def from_dict(cls, data: dict) -> Universe:
        """Deserialize a universe from a dict."""
        from .core.coord import Coord
        civs = [Civilization.from_dict(c) for c in data.get('civilizations', [])]
        return cls(
            width=data.get('width', 500.0),
            civilizations=civs,
            turn=data.get('turn', 0),
            event_log=list(data.get('event_log', [])),
            broadcast_signals=list(data.get('broadcast_signals', [])),
        )
