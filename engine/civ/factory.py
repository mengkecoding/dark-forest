"""CivilizationFactory — creates Civilization instances with randomized properties."""

from __future__ import annotations

import random
import uuid
from typing import Optional

from ..core.coord import Coord
from ..core.enums import Strategy as StrategyEnum
from ..core.state_machine import StateMachine

from .components.economy import EconomyComponent
from .components.military import MilitaryComponent
from .components.diplomacy import DiplomacyComponent
from .components.memory import MemoryComponent
from .traits import CivilizationTraits
from .strategies.hider import HiderStrategy
from .strategies.aggressor import AggressorStrategy
from .strategies.diplomat import DiplomatStrategy
from .strategies.observer import ObserverStrategy
from .strategies.cleaner import CleanerStrategy


# ── Name pools ──────────────────────────────────────────────

_HIDER_NAMES = ["三体人", "歌者文明", "归零者", "隐藏者α", "深海族", "暗影帝国"]
_AGGRESSOR_NAMES = ["魔眼文明", "边缘世界", "毁灭者Ω", "天狼帝国", "猎户联邦"]
_DIPLOMAT_NAMES = ["地球文明", "星际联邦", "和平使者", "银河议会"]
_OBSERVER_NAMES = ["观测者θ", "守望者", "记录者", "沉默舰队"]
_CLEANER_NAMES = ["清理者", "歌者", "清扫者Ω", "暗猎手"]

def reset_name_pools() -> None:
    """Reset the global name pools and used-names set."""
    global _NAME_POOLS, _USED_NAMES
    _NAME_POOLS = {
        StrategyEnum.HIDER: list(_HIDER_NAMES),
        StrategyEnum.AGGRESSOR: list(_AGGRESSOR_NAMES),
        StrategyEnum.DIPLOMAT: list(_DIPLOMAT_NAMES),
        StrategyEnum.OBSERVER: list(_OBSERVER_NAMES),
        StrategyEnum.CLEANER: list(_CLEANER_NAMES),
    }
    _USED_NAMES = set()

# Track used names globally so we can append "-N" suffixes on depletion
_USED_NAMES: set[str] = set()
_NAME_POOLS: dict = {}

reset_name_pools()  # initialize on module load

_STRATEGY_CLASSES = {
    StrategyEnum.HIDER: HiderStrategy,
    StrategyEnum.AGGRESSOR: AggressorStrategy,
    StrategyEnum.DIPLOMAT: DiplomatStrategy,
    StrategyEnum.OBSERVER: ObserverStrategy,
    StrategyEnum.CLEANER: CleanerStrategy,
}


def _pick_name(strategy: StrategyEnum) -> str:
    """Pick a unique name from the pool for the given strategy.

    When the pool is exhausted, names get a ``-N`` suffix.
    """
    pool = _NAME_POOLS[strategy]
    # Try original names first
    available = [n for n in pool if n not in _USED_NAMES]
    if available:
        name = random.choice(available)
        _USED_NAMES.add(name)
        return name

    # Exhausted — generate suffixed names
    suffix = 2
    while True:
        candidate = f"{pool[0]}-{suffix}"
        if candidate not in _USED_NAMES:
            _USED_NAMES.add(candidate)
            return candidate
        suffix += 1


def _random_traits() -> CivilizationTraits:
    """Generate randomized traits with each dimension uniform [0.1, 1.0]."""
    return CivilizationTraits(
        aggression=random.uniform(0.1, 1.0),
        honor=random.uniform(0.1, 1.0),
        resolve=random.uniform(0.1, 1.0),
        risk_taking=random.uniform(0.1, 1.0),
        expansionism=random.uniform(0.1, 1.0),
        paranoia=random.uniform(0.1, 1.0),
        strike_response=random.uniform(0.1, 1.0),
    )


class CivilizationFactory:
    """Factory for creating fully-formed Civilization instances."""

    @staticmethod
    def create(
        name: str | None,
        strategy: StrategyEnum,
        position: Coord,
        traits: CivilizationTraits | None = None,
    ) -> Civilization:
        """Build a new civilization with randomized components.

        Args:
            name: Display name. If None, a name is picked from the strategy pool.
            strategy: The civilization's survival strategy.
            position: Starting coordinate.
            traits: Optional pre-defined traits. If None, randomized.

        Returns:
            A fully initialized Civilization ready to participate in the sim.
        """
        from .civilization import Civilization  # late import to avoid circular

        if name is None:
            name = _pick_name(strategy)

        if traits is None:
            traits = _random_traits()

        civ_id = uuid.uuid4().hex[:8]

        # Base randomized components
        economy = EconomyComponent(
            population=random.uniform(30, 100),
            energy=random.uniform(200, 400),
            tech_level=random.uniform(1.0, 2.0),
        )
        military = MilitaryComponent(
            military_power=random.uniform(10, 30),
            stealth=0.5,
            detection_range=50.0,
            has_broadcast_capability=True,
        )
        diplomacy = DiplomacyComponent(reputation=0.5)
        memory = MemoryComponent()
        state_machine = StateMachine()

        # Strategy-specific bonuses
        strategy_instance = _STRATEGY_CLASSES[strategy]()

        if strategy == StrategyEnum.HIDER:
            military.stealth = 0.95
            military.detection_range *= 0.6
            military.has_broadcast_capability = False
        elif strategy == StrategyEnum.AGGRESSOR:
            military.military_power *= 1.8
            economy.energy += 200
            military.detection_range *= 1.3
        elif strategy == StrategyEnum.DIPLOMAT:
            diplomacy.reputation = 0.7
            military.stealth = 0.75
        elif strategy == StrategyEnum.OBSERVER:
            military.stealth = 0.9
            military.detection_range *= 1.3
            military.has_broadcast_capability = False
        elif strategy == StrategyEnum.CLEANER:
            military.stealth = 0.95
            traits.strike_response = 1.0
            military.military_power *= 2.0
            military.detection_range *= 2.0
            military.has_broadcast_capability = False

        # Re-clamp after modifications
        military.__post_init__()
        traits.__post_init__()

        return Civilization(
            id=civ_id,
            name=name,
            position=position,
            economy=economy,
            military=military,
            diplomacy=diplomacy,
            memory=memory,
            traits=traits,
            state_machine=state_machine,
            strategy=strategy_instance,
        )
