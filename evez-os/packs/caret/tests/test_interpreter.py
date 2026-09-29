import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = REPO / "game-agent-infra"
sys.path.insert(0, str(PACKAGE_ROOT))

SPEC = importlib.util.spec_from_file_location(
    "caret_lap_interpreter",
    REPO / "tools" / "caret_lap_interpreter.py",
)
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


def test_fixture_is_deterministic():
    path = REPO / "packs" / "caret" / "fixtures" / "demo_geometry.json"
    doc = json.loads(path.read_text())
    a = MOD.build(doc)
    b = MOD.build(doc)
    assert a["recursive_signature"]["signature"] == b["recursive_signature"]["signature"]
    assert a["input_symbol_count"] == 3
    assert a["evidence_status"] == "PROPOSED"
    assert a["result_sha256"]


def test_orientation_is_an_explicit_parameter():
    base = {"symbols":[{"id":"A","primitives":[{"kind":"stroke","points":[[0,0],[10,0]]}]}]}
    rotated = {"symbols":[{"id":"A","primitives":[{"kind":"stroke","points":[[0,0],[0,10]]}]}]}
    a = MOD.build(base)
    b = MOD.build(rotated)
    assert a["symbols"][0]["descriptor"]["orientation_deg"] != b["symbols"][0]["descriptor"]["orientation_deg"]
    assert a["input_symbol_count"] == b["input_symbol_count"] == 1
