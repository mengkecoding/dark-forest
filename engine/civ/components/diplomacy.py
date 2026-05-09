"""Diplomacy component — reputation, treaties, deterrence, chain-of-suspicion."""

from __future__ import annotations

from dataclasses import dataclass, field

from ...core.enums import TreatyType


@dataclass
class Treaty:
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
    """Diplomatic state including chain-of-suspicion tracking."""

    reputation: float = 0.5
    treaties: dict[str, Treaty] = field(default_factory=dict)
    communication_log: list[str] = field(default_factory=list)
    deterrence_declared: bool = False
    deterrence_target: str = ''
    suspicion_level: float = 0.0
    suspicion_targets: dict[str, float] = field(default_factory=dict)

    def propose_treaty(self, target_id: str, treaty_type: TreatyType) -> Treaty:
        treaty = Treaty(type=treaty_type, partner_id=target_id, turns_remaining=50)
        self.treaties[target_id] = treaty
        return treaty

    def break_treaty(self, target_id: str) -> None:
        self.reputation = 0.0
        self.treaties.pop(target_id, None)

    def tick_treaties(self) -> None:
        expired = [pid for pid, t in self.treaties.items() if t.turns_remaining <= 1]
        for pid in expired:
            del self.treaties[pid]
        for t in self.treaties.values():
            t.turns_remaining -= 1

    def tick_suspicion(self, paranoia: float, known_civ_ids: list[str],
                        name_lookup: dict = None) -> list[str]:
        """Escalate suspicion each turn for every known neighbor.

        Suspicion grows proportional to paranoia trait.
        Returns list of human-readable log messages.
        """
        messages = []
        for cid in known_civ_ids:
            prev = self.suspicion_targets.get(cid, 0.0)
            growth = 0.01 + paranoia * 0.03  # 1-4% per turn
            new_val = min(1.0, prev + growth)
            self.suspicion_targets[cid] = new_val

            # Log when crossing a chain level
            for threshold, label in [(0.25, 'L1'), (0.5, 'L2'), (0.75, 'L3')]:
                if prev < threshold <= new_val:
                    display = name_lookup.get(cid, cid[:6]) if name_lookup else cid[:6]
                    messages.append(f'猜疑链升级: 对{display}达到{label}')

        self.suspicion_level = sum(self.suspicion_targets.values()) / max(len(self.suspicion_targets), 1)
        return messages

    def evaluate_trust(
        self, target_reputation: float, target_id: str,
    ) -> float:
        """Compute trust with chain-of-suspicion and trust dice.

        Formula: rep * (1 - suspicion) + random_dice(-0.15, +0.15)
        """
        import random
        susp = self.suspicion_targets.get(target_id, 0.0)
        base = target_reputation * (1.0 - susp * 0.7)
        dice = random.uniform(-0.12, 0.12)
        return max(0.0, min(1.0, base + dice))

    def suspicion_label(self) -> str:
        """Human-readable suspicion level."""
        if self.suspicion_level < 0.2:
            return 'L0 信任'
        elif self.suspicion_level < 0.4:
            return 'L1 警觉'
        elif self.suspicion_level < 0.6:
            return 'L2 猜疑'
        elif self.suspicion_level < 0.8:
            return 'L3 深度猜疑'
        return 'L4 黑暗森林'

    def to_dict(self) -> dict:
        return {
            'reputation': self.reputation,
            'treaties': {k: v.to_dict() for k, v in self.treaties.items()},
            'communication_log': list(self.communication_log),
            'deterrence_declared': self.deterrence_declared,
            'deterrence_target': self.deterrence_target,
            'suspicion_level': self.suspicion_level,
            'suspicion_targets': dict(self.suspicion_targets),
        }

    @classmethod
    def from_dict(cls, data: dict) -> DiplomacyComponent:
        treaties = {k: Treaty.from_dict(v) for k, v in data.get('treaties', {}).items()}
        return cls(
            reputation=data['reputation'],
            treaties=treaties,
            communication_log=list(data.get('communication_log', [])),
            deterrence_declared=data.get('deterrence_declared', False),
            deterrence_target=data.get('deterrence_target', ''),
            suspicion_level=data.get('suspicion_level', 0.0),
            suspicion_targets=data.get('suspicion_targets', {}),
        )
