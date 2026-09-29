import importlib.util
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

canon=load("canon",ROOT/"tools"/"caret_canonical_signature.py")
inv=load("inv",ROOT/"tools"/"caret_invariance_battery.py")

def test_canonical_signature_ignores_similarity_transform():
    doc=json.loads((ROOT/"packs"/"caret"/"fixtures"/"demo_geometry.json").read_text())
    variants=[
        doc,
        inv.transform(doc,theta=math.pi/4),
        inv.transform(doc,reflect_x=True),
        inv.transform(doc,scale=7.0,dx=1234.0,dy=-77.0),
    ]
    sigs=[canon.canonical(x)[1] for x in variants]
    assert len(set(sigs))==1
