from __future__ import annotations

import json
import os
import subprocess
import sys


def run_cli(db_path, *args):
    env = {**os.environ, "PYTHONPATH": "src"}
    result = subprocess.run([sys.executable, "-m", "portfolio_os.cli.main", "--db", str(db_path), *args], cwd=os.getcwd(), env=env, text=True, capture_output=True, check=True)
    return result.stdout.strip()


def test_stage2_cli_smoke_seed_policy(tmp_path) -> None:
    db_path = tmp_path / "stage2_cli.sqlite3"
    run_cli(db_path, "init-db")
    output = json.loads(run_cli(db_path, "seed-default-risk-policy", "--base-currency", "CHF"))
    assert output["policy_version_id"] == 1
