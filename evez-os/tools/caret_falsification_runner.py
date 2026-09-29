#!/usr/bin/env python3
"""
CARET adversarial runner.

Runs:
  parser
  canonical signature
  invariance battery
  anti-pareidolia null model
  quantum speedrun

Program synthesis is intentionally omitted here because it is expensive.
Run caret_program_synth.py separately or from CI.

This runner is designed to answer a harder question:
"Does the structure survive hostile tests, or does it disappear when we
change the representation and compare against null models?"
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

HERE=Path(__file__).resolve()
TOOLS=HERE.parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    assert spec.loader
    spec.loader.exec_module(m)
    return m

def digest(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o","--output",default="caret_falsification_report.json")
    ap.add_argument("--permutations",type=int,default=5000)
    args=ap.parse_args()

    doc=json.loads(Path(args.input).read_text())
    interp=load("caret_lap_interpreter",TOOLS/"caret_lap_interpreter.py")
    canon=load("caret_canonical_signature",TOOLS/"caret_canonical_signature.py")
    inv=load("caret_invariance_battery",TOOLS/"caret_invariance_battery.py")
    anti=load("caret_pareidolia_gate",TOOLS/"caret_pareidolia_gate.py")
    quantum=load("caret_quantum_speedrun",TOOLS/"caret_quantum_speedrun.py")

    parsed=interp.build(doc)
    _, canonical_signature=canon.canonical(doc)
    inv_report=inv.run(doc)
    anti_report=anti.run(parsed,permutations=args.permutations,seed=1337)
    q=quantum.speedrun(doc)

    report={
        "engine":"EVEZ-CARET-Adversarial-Runner",
        "evidence_status":"PROPOSED",
        "input_sha256":digest(doc),
        "canonical_signature":canonical_signature,
        "invariance":inv_report,
        "anti_pareidolia":anti_report,
        "quantum_speedrun":{
            "best_entropy_bits":q["best_by_entropy"]["entropy_bits"],
            "best_rotation_deg":q["best_by_entropy"]["rotation_deg"],
            "best_circuit_sha256":q["best_by_entropy"]["circuit_sha256"],
        },
        "decision_gate":{
            "extraterrestrial_origin":"UNKNOWN",
            "semantic_decode":"UNKNOWN",
            "physical_effect":"UNKNOWN",
            "computational_structure":"MEASURED",
            "promotion_rule":"Only independently replicated observations can promote UNKNOWN claims."
        }
    }
    report["report_sha256"]=digest(report)
    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
        "report":args.output,
        "canonical_signature":canonical_signature,
        "empirical_p_value":anti_report["empirical_p_value"],
        "null_z":anti_report["null_z"],
        "invariants":inv_report["invariant_variants"],
        "quantum_entropy_bits":q["best_by_entropy"]["entropy_bits"],
        "report_sha256":report["report_sha256"]
    },indent=2))

if __name__=="__main__":
    main()
