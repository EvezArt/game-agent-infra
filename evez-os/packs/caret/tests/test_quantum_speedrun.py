import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location("speed",ROOT/"tools"/"caret_quantum_speedrun.py")
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def test_quantum_speedrun_is_deterministic():
    doc=json.loads((ROOT/"packs"/"caret"/"fixtures"/"demo_geometry.json").read_text())
    a=m.speedrun(doc)
    b=m.speedrun(doc)
    assert a["best_by_entropy"]["circuit_sha256"]==b["best_by_entropy"]["circuit_sha256"]
    assert a["best_by_entropy"]["basis_signature"]==b["best_by_entropy"]["basis_signature"]
    assert len(a["all_runs"])==8

def test_statevector_is_normalized():
    state=m.run_circuit(2,[("H",0),("CPHASE",0,1,3.141592653589793)])
    z=sum(abs(x)**2 for x in state)
    assert abs(z-1.0)<1e-12
