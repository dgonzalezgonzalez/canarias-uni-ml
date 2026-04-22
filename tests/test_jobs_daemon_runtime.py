import os

import pytest

from src.canarias_uni_ml.jobs.daemon import DaemonLock, run_jobs_daemon


def test_daemon_lock_blocks_when_process_alive(tmp_path):
    lock_path = tmp_path / "daemon.lock"
    lock_path.write_text(str(os.getpid()), encoding="utf-8")
    lock = DaemonLock(lock_path)
    with pytest.raises(RuntimeError):
        lock.acquire()


def test_daemon_lock_reclaims_stale_pid(tmp_path):
    lock_path = tmp_path / "daemon.lock"
    lock_path.write_text("999999", encoding="utf-8")
    lock = DaemonLock(lock_path)
    lock.acquire()
    assert lock_path.exists()
    lock.release()
    assert not lock_path.exists()


def test_run_jobs_daemon_run_once_executes_single_cycle(tmp_path, monkeypatch):
    calls: list[dict[str, object]] = []

    def fake_run_jobs_pipeline(**kwargs):
        calls.append(kwargs)
        return 0

    monkeypatch.setattr("src.canarias_uni_ml.jobs.daemon.run_jobs_pipeline", fake_run_jobs_pipeline)

    code = run_jobs_daemon(
        limit_per_source=5,
        output_path=str(tmp_path / "jobs.csv"),
        db_path=str(tmp_path / "jobs.db"),
        window_start="00:00",
        window_end="23:59",
        timezone_name="Europe/Madrid",
        run_once=True,
        lock_path=str(tmp_path / "daemon.lock"),
    )
    assert code == 0
    assert len(calls) == 1
