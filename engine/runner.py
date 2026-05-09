"""Simulation runner — turn lifecycle, action dispatch, snapshotting."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

from .config import SimulationConfig
from .universe import Universe
from .core.coord import Coord
from .core.enums import Action, Strategy, CivState, WeaponType, TreatyType
from .core.events import EventBus
from .civ.civilization import Civilization
from .civ.factory import CivilizationFactory


@dataclass
class SimulationRunner:
    """Orchestrates the entire dark forest simulation.

    Usage:
        runner = SimulationRunner(SimulationConfig())
        history = runner.run_simulation(max_turns=100)
    """

    config: SimulationConfig
    universe: Universe = field(init=False)

    def __post_init__(self) -> None:
        self.universe = Universe(width=self.config.universe_width)
        self.create_civilizations()

    # ── Civilization creation ──────────────────────────────

    def create_civilizations(self) -> list[Civilization]:
        """Use CivilizationFactory to spawn all civs at random non-overlapping positions."""
        from .civ.factory import reset_name_pools
        reset_name_pools()
        civs: list[Civilization] = []
        total = self.config.total_civs

        strategy_counts = [
            (Strategy.HIDER, self.config.hider_count),
            (Strategy.AGGRESSOR, self.config.aggressor_count),
            (Strategy.DIPLOMAT, self.config.diplomat_count),
            (Strategy.OBSERVER, self.config.observer_count),
            (Strategy.CLEANER, self.config.cleaner_count),
        ]

        for strategy, count in strategy_counts:
            for _ in range(count):
                pos = self._random_position(civs)
                civ = CivilizationFactory.create(
                    name=None,
                    strategy=strategy,
                    position=pos,
                )
                civs.append(civ)

        random.shuffle(civs)
        self.universe.civilizations = civs

        for civ in civs:
            self.universe.log_event(f'{civ.name}（{civ.strategy.label}）出现在 ({civ.position.x:.0f}, {civ.position.y:.0f})')

        return civs

    def _random_position(self, existing: list[Civilization]) -> Coord:
        """Generate a random position at least min_spawn_distance from existing civs."""
        max_attempts = 200
        width = self.config.universe_width
        min_dist = self.config.min_spawn_distance

        for _ in range(max_attempts):
            x = random.uniform(0, width)
            y = random.uniform(0, width)
            pos = Coord(x, y)

            too_close = False
            for other in existing:
                dist = pos.distance_to(other.position, width=width)
                if dist < min_dist:
                    too_close = True
                    break

            if not too_close:
                return pos

        # Fallback: place anywhere
        return Coord(random.uniform(0, width), random.uniform(0, width))

    # ── Turn lifecycle ─────────────────────────────────────

    def run_turn(self) -> dict:
        """Execute one full simulation turn. Returns snapshot dict."""
        self.universe.turn += 1
        turn = self.universe.turn

        # 1. Detect broadcast signals (all civs check global broadcast list)
        for civ in self._active_civs():
            from .systems import detection
            detection.detect_broadcasts(civ, self.universe)

        # 2. Shuffle active civs
        active = self._active_civs()
        random.shuffle(active)

        # 4. Each civ: decide() + execute()
        for civ in active:
            if civ.is_destroyed:
                continue

            action = civ.decide(self.universe)
            self._execute(civ, action)

        # Process pending broadcast strikes (after civs have seen them)
        signals_to_process = list(self.universe.broadcast_signals)
        self.universe.broadcast_signals.clear()
        for signal in signals_to_process:
            target = self._find_civ(signal.get('target_id', ''))
            if target and not target.is_destroyed:
                from .systems import broadcast_strike
                broadcast_strike.process_global_strikes(target, self.universe)

        # 5. Process economy (maintenance + breakthrough checks)
        for civ in self._active_civs():
            from .systems.economy import process_economy, process_breakthrough
            process_economy(civ, self.universe)
            process_breakthrough(civ, self.universe)

        # 6. Process arms race for ALERT civs
        for civ in self._active_civs():
            from .systems import arms_race
            arms_race.process_arms_race(civ, self.universe)

        # 7. Process chain exposure
        for civ in self._active_civs():
            from .systems import chain_exposure
            chain_exposure.propagate_exposure(civ, self.universe)

        # 8. Tick treaties
        for civ in self._active_civs():
            from .systems import diplomacy
            diplomacy.tick_treaties(civ, self.universe)

        # 9. Take snapshot
        return self.take_snapshot()

    # ── Action dispatch ────────────────────────────────────

    def _execute(self, civ: Civilization, action: Action) -> None:
        """Dispatch a decided Action to the appropriate system function.

        This is the INTEGRATION POINT — maps Action enums to system function calls.
        """
        civ.turns_alive += 1

        if action == Action.NOTHING:
            return

        elif action == Action.DETECT:
            from .systems import detection
            detection.process_detection(civ, self.universe)
            civ.economy.energy = max(0.0, civ.economy.energy - 5.0)

        elif action == Action.ATTACK:
            self._dispatch_attack(civ)

        elif action == Action.BROADCAST_TARGET:
            target = self._pick_broadcast_target(civ)
            if target:
                from .systems import broadcast_strike
                broadcast_strike.broadcast_target_coords(civ, target, self.universe)
            else:
                civ.military.reduce_stealth(0.05)

        elif action == Action.BROADCAST_SELF:
            civ.military.reduce_stealth(civ.military.stealth * 0.9)  # drop to ~0.1
            civ.military.has_broadcast_capability = True
            self.universe.log_event(f'{civ.name} 向宇宙广播了自己的存在！')

        elif action == Action.COMMUNICATE:
            target = self._pick_communicate_target(civ)
            if target:
                from .systems import diplomacy
                diplomacy.process_communication(civ, target, self.universe)

        elif action == Action.PROPOSE_TREATY:
            target = self._pick_treaty_target(civ)
            if target:
                from .systems import diplomacy
                # Propose non-aggression by default, upgrade existing
                existing = civ.diplomacy.treaties.get(target.id)
                treaty_type = TreatyType.NON_AGGRESSION
                if existing:
                    if existing.type == TreatyType.NON_AGGRESSION:
                        treaty_type = TreatyType.TRADE
                    elif existing.type == TreatyType.TRADE:
                        treaty_type = TreatyType.ALLIANCE
                diplomacy.process_treaty_proposal(civ, target, treaty_type, self.universe)
            civ.economy.energy = max(0.0, civ.economy.energy - 10.0)

        elif action == Action.BREAK_TREATY:
            target_id = self._pick_break_target(civ)
            if target_id:
                from .systems import diplomacy
                diplomacy.process_break_treaty(civ, target_id, self.universe)

        elif action == Action.DECLARE_DETERRENCE:
            target = self._pick_deterrence_target(civ)
            if target:
                from .systems import deterrence
                deterrence.declare_deterrence(civ, target, self.universe)
            civ.diplomacy.deterrence_declared = True

        elif action == Action.HIDE:
            civ.military.increase_stealth(0.03)
            civ.economy.energy = max(0.0, civ.economy.energy - 5.0)

        elif action == Action.EXPAND:
            civ.economy.grow()

        elif action == Action.RESEARCH:
            civ.economy.research(civ.military)

        # Always run maintenance after action
        civ.economy.maintenance()

    def _dispatch_attack(self, civ: Civilization) -> None:
        """Choose a target and weapon, then resolve the attack."""
        target = self._pick_attack_target(civ)
        if target is None:
            civ.economy.energy = max(0.0, civ.economy.energy - 30.0)
            return

        # Track recent attacks to avoid spamming same target
        if not hasattr(civ, '_recent_attack_targets'):
            civ._recent_attack_targets = set()
        civ._recent_attack_targets.add(target.id)
        # Keep only last 3 to avoid unlimited growth
        if len(civ._recent_attack_targets) > 3:
            civ._recent_attack_targets = set(list(civ._recent_attack_targets)[-3:])

        weapon = civ.military.choose_weapon(target.economy.tech_level, civ.traits)

        # Check for preventive strike scenario
        from .systems import breakthrough as b_sys
        if b_sys.check_preventive_strike(civ, target, self.universe):
            self.universe.log_event(f'{civ.name} 对 {target.name} 发动预防性打击')

        from .systems import combat
        success = combat.resolve_attack(civ, target, self.universe, weapon=weapon)

        if success:
            # Reverse engineer
            b_sys.apply_reverse_engineering(civ, target, self.universe)

            # Chain exposure
            from .systems import chain_exposure
            chain_exposure.on_attack_exposed(civ, self.universe)
            chain_exposure.on_destruction_exposed(target, civ.name, self.universe)

    # ── Target selection helpers ───────────────────────────

    def _pick_attack_target(self, civ: Civilization) -> Civilization | None:
        """Pick attack target. Cleaners prioritize broadcasters, others pick weakest."""
        from .core.enums import Strategy as StratEnum
        candidates: list[tuple[float, Civilization]] = []

        is_cleaner = getattr(civ.strategy, 'label', '') == '清理者'

        for cid in civ.memory.known_civs:
            other = self._find_civ(cid)
            if other and not other.is_destroyed:
                priority = 0.0
                if is_cleaner and other.military.stealth < 0.15:
                    priority = 1000.0  # broadcast target → highest priority
                candidates.append((other.military.military_power - priority, other))

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    def _pick_broadcast_target(self, civ: Civilization) -> Civilization | None:
        """Pick strongest known target to broadcast."""
        candidates: list[tuple[float, Civilization]] = []
        for cid in civ.memory.known_civs:
            other = self._find_civ(cid)
            if other and not other.is_destroyed:
                candidates.append((other.military.military_power, other))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def _pick_communicate_target(self, civ: Civilization) -> Civilization | None:
        """Pick first known civ not already communicated with."""
        for cid in civ.memory.known_civs:
            other = self._find_civ(cid)
            if other and not other.is_destroyed:
                return other
        return None

    def _pick_treaty_target(self, civ: Civilization) -> Civilization | None:
        """Pick a known civ not already in a treaty (or upgrade candidate)."""
        for cid in civ.memory.known_civs:
            other = self._find_civ(cid)
            if other and not other.is_destroyed:
                return other
        return None

    def _pick_break_target(self, civ: Civilization) -> str | None:
        """Pick first active treaty partner to break."""
        for cid in civ.diplomacy.treaties:
            return cid
        return None

    def _pick_deterrence_target(self, civ: Civilization) -> Civilization | None:
        """Pick the most threatening known civ."""
        candidates: list[tuple[float, Civilization]] = []
        for cid in civ.memory.known_civs:
            other = self._find_civ(cid)
            if other and not other.is_destroyed:
                candidates.append((other.military.military_power, other))
        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    # ── Simulation loop ────────────────────────────────────

    def run_simulation(self, max_turns: int | None = None) -> list[dict]:
        """Run until max_turns or 1 survivor or 80 turns of no events.

        Returns list of turn snapshots.
        """
        max_t = max_turns if max_turns is not None else self.config.max_turns
        snapshots: list[dict] = []
        no_event_streak = 0
        last_log_len = 0

        for _ in range(max_t):
            snapshot = self.run_turn()
            snapshots.append(snapshot)

            # Check survivors
            active = self._active_civs()
            if len(active) <= 1:
                self.universe.log_event(f'🏆 宇宙仅剩 {len(active)} 个文明存活！')
                break

            # Check for event stagnation
            if len(self.universe.event_log) == last_log_len:
                no_event_streak += 1
            else:
                no_event_streak = 0
                last_log_len = len(self.universe.event_log)

            if no_event_streak >= 80:
                self.universe.log_event('宇宙进入长久的沉默... 模拟终止')
                break

        return snapshots

    # ── Utilities ──────────────────────────────────────────

    def _active_civs(self) -> list[Civilization]:
        """Return all non-destroyed civilizations."""
        return [c for c in self.universe.civilizations if not c.is_destroyed]

    def _find_civ(self, civ_id: str) -> Civilization | None:
        for c in self.universe.civilizations:
            if c.id == civ_id:
                return c
        return None

    def take_snapshot(self) -> dict:
        """Return a summary snapshot of the current turn."""
        active = self._active_civs()
        destroyed = [c for c in self.universe.civilizations if c.is_destroyed]

        return {
            'turn': self.universe.turn,
            'active_count': len(active),
            'destroyed_count': len(destroyed),
            'civilizations': [c.to_dict() for c in self.universe.civilizations],  # ALL civs
            'event_log': list(self.universe.event_log)[-30:],  # last 30 events
            'total_events': len(self.universe.event_log),
        }

    def to_json(self) -> str:
        """Serialize the full simulation state to a JSON string."""
        return json.dumps(self.universe.to_dict(), ensure_ascii=False, indent=2)
