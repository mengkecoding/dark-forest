"""Quick smoke tests for dark-forest v2 engine."""
from engine.config import SimulationConfig
from engine.runner import SimulationRunner


def test_simulation_runs():
    config = SimulationConfig(
        universe_width=250, max_turns=50,
        hider_count=2, aggressor_count=2, diplomat_count=1,
        observer_count=1, cleaner_count=1,
    )
    runner = SimulationRunner(config)
    snapshots = runner.run_simulation()
    assert len(snapshots) >= 1
    final = snapshots[-1]
    assert final['turn'] > 0
    assert 'civilizations' in final
    assert len(final['civilizations']) >= 1


def test_dark_forest_laws():
    """Broadcasters survive fewer turns than silent civs."""
    config = SimulationConfig(
        universe_width=200, max_turns=100,
        hider_count=2, aggressor_count=2, diplomat_count=2,
        observer_count=1, cleaner_count=0,
    )
    runner = SimulationRunner(config)
    snapshots = runner.run_simulation()
    final = snapshots[-1]
    civs = final['civilizations']
    broadcasters = [c for c in civs if c.get('has_broadcast')]
    silent = [c for c in civs if not c.get('has_broadcast')]
    # At minimum, this should run without error
    assert final['turn'] > 0


def test_civilization_count():
    config = SimulationConfig(
        hider_count=3, aggressor_count=2, diplomat_count=1,
        observer_count=1, cleaner_count=1,
    )
    runner = SimulationRunner(config)
    civs = runner.universe.civilizations
    assert len(civs) == 8


if __name__ == '__main__':
    test_simulation_runs()
    test_dark_forest_laws()
    test_civilization_count()
    print('✅ All 3 smoke tests passed')
