"""Diplomacy component — reputation, treaties, deterrence, and trust."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...core.enums import TreatyType


@dataclass
class Treaty:
    """A diplomatic agreement between two civilizations.

    Attributes:
        type: The treaty category (non_aggression, alliance, trade).
        partner_id: The other civilization's id.
        turns_remaining: Turns until the treaty expires naturally.
        signed_on_turn: The simulation turn when the treaty was signed.
    """

    type: TreatyType
    partner_id: str
    turns_remaining: int = 50
    signed_on_turn: int = 0

    def to_dict(self) -> dict:
        return {
            'type': self.type.value,
            'partner_id': self.partner_id,
            'turns_remaining': self.turns_remaining,
            'signed_on_turn': self.signed_on_turn,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Treaty:
        return cls(
            type=TreatyType(data['type']),
            partner_id=data['partner_id'],
            turns_remaining=data['turns_remaining'],
            signed_on_turn=data['signed_on_turn'],
        )


@dataclass
class DiplomacyComponent:
    """Tracks a civilization's diplomatic state: reputation, treaties, deterrence.

    Attributes:
        reputation: Global standing, clamped [0.0, 1.0].
        treaties: Active treaties keyed by partner_id.
        communication_log: List of recent communication messages (str).
        deterrence_declared: Whether this civ has declared deterrence against someone.
        deterrence_target: The id of the deterrence target (empty if none).
    """

    reputation: float = 0.5
    treaties: dict[str, Treaty] = field(default_factory=dict)
    communication_log: list[str] = field(default_factory=list)
    deterrence_declared: bool = False
    deterrence_target: str = ''

    def propose_treaty(self, target_id: str, treaty_type: TreatyType) -> Treaty:
        """Create a proposed treaty with *target_id* (turns_remaining=50).

        The treaty is stored in self.treaties.  In a full sim the target must
        accept for it to be active; this method represents the offer side.

        Args:
            target_id: The other civilization's id.
            treaty_type: The kind of treaty being proposed.

        Returns:
            The newly created Treaty object.
        """
        treaty = Treaty(type=treaty_type, partner_id=target_id, turns_remaining=50)
        self.treaties[target_id] = treaty
        return treaty

    def break_treaty(self, target_id: str) -> None:
        """Break a treaty with *target_id* — reputation drops to 0, treaty removed.

        In a full sim this should also emit a betrayal broadcast.
        """
        self.reputation = 0.0
        self.treaties.pop(target_id, None)

    def tick_treaties(self) -> None:
        """Decrement turns_remaining on all active treaties; remove expired ones."""
        expired = [
            pid for pid, t in self.treaties.items()
            if t.turns_remaining <= 1
        ]
        for pid in expired:
            del self.treaties[pid]
        for t in self.treaties.values():
            t.turns_remaining -= 1

    def evaluate_trust(
        self, target_reputation: float, suspicion_level: float,
    ) -> float:
        """Compute how much this civ trusts another, given their reputation and
        this civ's suspicion level (derived from traits.paranoia).

        Returns a trust score in [0.0, 1.0].

        Args:
            target_reputation: The other civilization's reputation [0,1].
            suspicion_level: This civ's paranoia/suspicion [0,1].

        Returns:
            Trust score: target_reputation * (1 - suspicion_level).
        """
        raw = target_reputation * (1.0 - suspicion_level)
        return max(0.0, min(1.0, raw))

    def to_dict(self) -> dict:
        """Serialize to plain dict."""
        return {
            'reputation': self.reputation,
            'treaties': {k: v.to_dict() for k, v in self.treaties.items()},
            'communication_log': list(self.communication_log),
            'deterrence_declared': self.deterrence_declared,
            'deterrence_target': self.deterrence_target,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DiplomacyComponent:
        """Deserialize from dict."""
        treaties = {
            k: Treaty.from_dict(v) for k, v in data.get('treaties', {}).items()
        }
        return cls(
            reputation=data['reputation'],
            treaties=treaties,
            communication_log=list(data.get('communication_log', [])),
            deterrence_declared=data.get('deterrence_declared', False),
            deterrence_target=data.get('deterrence_target', ''),
        )
