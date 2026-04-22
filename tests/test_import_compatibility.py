from src.canarias_jobs.cli import run


def test_legacy_cli_run_symbol_exists():
    assert callable(run)
