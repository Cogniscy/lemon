"""Run with the wheel environment's Python from any working directory."""
import json
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import lemon_factor

repo = Path(__file__).resolve().parents[1]
assert not Path(lemon_factor.__file__).resolve().is_relative_to(repo / "src"), "Imported checkout"

with tempfile.TemporaryDirectory() as directory:
    output = subprocess.check_output(
        [sys.executable, "-I", "-m", "lemon_factor", "demo", "--format", "json"],
        cwd=directory, text=True,
    )
    report = json.loads(output)
    assert len(report["cases"]) == 4
    subprocess.run(
        [sys.executable, "-I", "-m", "lemon_factor", "reproduce-demo", "--out", "results"],
        cwd=directory, check=True,
    )
    assert json.loads((Path(directory) / "results/scores.json").read_text()) == report

def no_network(*args, **kwargs):
    raise AssertionError("Unexpected network access")
socket.socket = no_network
socket.create_connection = no_network
from lemon_factor.demo import build_demo
assert build_demo() == report
from importlib.resources import files
assert files("lemon_factor.llm").joinpath("prompts/decompose_predicate.md").is_file()
print("Installed wheel: offline demo, reproduction and packaged prompts OK")
