"""Simulation configuration — tunable parameters for the dark forest sim."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SimulationConfig:
    """All knobs for a simulation run."""

    # ── Universe ──────────────────────────────────────────
    universe_width: float = 500.0
    max_turns: int = 500
    min_spawn_distance: float = 20.0

    # ── Civilization counts per strategy ─────────────────
    hider_count: int = 4
    aggressor_count: int = 3
    diplomat_count: int = 2
    observer_count: int = 2
    cleaner_count: int = 1

    # ── Initial resource ranges ──────────────────────────
    initial_population_range: tuple[float, float] = (30.0, 100.0)
    initial_energy_range: tuple[float, float] = (200.0, 400.0)
    initial_tech_range: tuple[float, float] = (1.0, 2.0)
    initial_military_range: tuple[float, float] = (10.0, 30.0)

    # ── Detection ─────────────────────────────────────────
    base_detection_range: float = 60.0
    detection_prob_factor: float = 0.6  # stealth * factor subtracted from 1.0

    # ── Combat ────────────────────────────────────────────
    attack_base_prob: float = 0.35
    attack_cap: float = 0.88

    # ── Breakthrough ──────────────────────────────────────
    breakthrough_base_chance: float = 0.015
    breakthrough_magnitude_min: float = 1.5
    breakthrough_magnitude_max: float = 3.0

    # ── Economy ───────────────────────────────────────────
    maintenance_rate: float = 0.015  # energy -= population * rate
    research_cost: float = 18.0
    expand_cost: float = 20.0

    @property
    def total_civs(self) -> int:
        return (
            self.hider_count + self.aggressor_count +
            self.diplomat_count + self.observer_count +
            self.cleaner_count
        )

    def to_dict(self) -> dict:
        return {
            'universe_width': self.universe_width,
            'max_turns': self.max_turns,
            'min_spawn_distance': self.min_spawn_distance,
            'hider_count': self.hider_count,
            'aggressor_count': self.aggressor_count,
            'diplomat_count': self.diplomat_count,
            'observer_count': self.observer_count,
            'cleaner_count': self.cleaner_count,
            'initial_population_range': list(self.initial_population_range),
            'initial_energy_range': list(self.initial_energy_range),
            'initial_tech_range': list(self.initial_tech_range),
            'initial_military_range': list(self.initial_military_range),
            'base_detection_range': self.base_detection_range,
            'detection_prob_factor': self.detection_prob_factor,
            'attack_base_prob': self.attack_base_prob,
            'attack_cap': self.attack_cap,
            'breakthrough_base_chance': self.breakthrough_base_chance,
            'breakthrough_magnitude_min': self.breakthrough_magnitude_min,
            'breakthrough_magnitude_max': self.breakthrough_magnitude_max,
            'maintenance_rate': self.maintenance_rate,
            'research_cost': self.research_cost,
            'expand_cost': self.expand_cost,
        }
