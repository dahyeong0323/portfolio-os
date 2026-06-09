from __future__ import annotations

import os
import subprocess
import sys


def test_cli_init_db_and_ledger_status(tmp_path) -> None:
    db_path = tmp_path / "cli.sqlite3"
    env = {**os.environ, "PYTHONPATH": "src"}
    init = subprocess.run(
        [sys.executable, "-m", "portfolio_os.cli.main", "--db", str(db_path), "init-db"],
        cwd=os.getcwd(),
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "initialized" in init.stdout
    status = subprocess.run(
        [sys.executable, "-m", "portfolio_os.cli.main", "--db", str(db_path), "ledger-status"],
        cwd=os.getcwd(),
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    assert status.stdout.strip() == "provisional"
