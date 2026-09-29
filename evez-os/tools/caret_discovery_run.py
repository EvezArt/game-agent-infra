#!/usr/bin/env python3
"""
One-command CARET discovery runner.

Stages:
  1. Geometry parse
  2. Invariance battery
  3. Candidate quantum-program synthesis
  4. Cross-stage evidence record
  5. Append-only spine event

This is deliberately evidence-first: every generated interpretation remains PROPOSED.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path

HERE=Path(__file__).resolve()
TOOLS=HERE.parent
ROOT=HERE.parents[2]

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
    ap.add_argument("-o","--output",default="caret_discovery_report.json")
    ap.add_argument("--topk",type=int,default=12)
    ap.add_argument("--spine")
    args=ap.parse_args()

    doc=json.loads(Path(args.input).read_text())
    interp=load("caret_lap_interpreter",TOOLS/"caret_lap_interpreter.py")
    quantum=load("caret_quantum_speedrun",TOOLS/"caret_quantum_speedrun.py")
    synth=load("caret_program_synth",TOOLS/"caret_program_synth.py")
    invariance=load("caret_invariance_battery",TOOLS/"caret_invariance_battery.py")

    parse=interp.build(doc)
    q=quantum.speedrun(doc)
    inv=invariance.run(doc)

    # Program synthesis is intentionally optional for huge future inputs.
    # The finite search remains deterministic.
    syn=synth.synth(doc,topk=args.topk,scan=True)

    report={
        "engine":"EVEZ-CARET-Discovery-Runner",
        "evidence_status":"PROPOSED",
        "input_sha256":digest(doc),
        "parse":{
            "symbol_count":parse["input_symbol_count"],
            "relation_count":len(parse["relations"]),
            "recursive_signature":parse["recursive_signature"]["signature"],
            "result_sha256":parse["result_sha256"],
        },
        "quantum_speedrun":{
            "best_entropy_bits":q["best_by_entropy"]["entropy_bits"],
            "best_circuit_sha256":q["best_by_entropy"]["circuit_sha256"],
            "best_rotation_deg":q["best_by_entropy"]["rotation_deg"],
            "result_sha256":q["result_sha256"],
        },
        "invariance":{
            "invariant_variants":inv["invariant_variants"],
            "sensitive_variants":inv["sensitive_variants"],
            "result_sha256":inv["result_sha256"],
        },
        "program_synthesis":{
            "search_space":syn["search_space"],
            "topk":syn["topk"],
            "result_sha256":syn["result_sha256"],
        },
        "epistemic_gate":{
            "physical_effect_verified":False,
            "extraterrestrial_origin_verified":False,
            "semantic_decode_verified":False,
            "rule":"Generated structures remain hypotheses until independent evidence promotes them."
        }
    }
    report["report_sha256"]=digest(report)

    if args.spine:
        package=ROOT/"game-agent-infra"
        sys.path.insert(0,str(package))
        from game_agent_infra.core.spine import AppendOnlySpine
        spine=AppendOnlySpine(Path(args.spine))
        ev=spine.append({
            "agent_id":"caret-discovery",
            "anomaly":"caret_lap_discovery_run",
            "status":report["evidence_status"],
            "input_sha256":report["input_sha256"],
            "report_sha256":report["report_sha256"],
            "recursive_signature":report["parse"]["recursive_signature"],
        })
        report["spine_event_hash"]=ev.hash
        report["report_sha256"]=digest(report)

    Path(args.output).write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({
        "report":args.output,
        "input_sha256":report["input_sha256"],
        "recursive_signature":report["parse"]["recursive_signature"],
        "best_entropy_bits":report["quantum_speedrun"]["best_entropy_bits"],
        "invariants":report["invariance"]["invariant_variants"],
        "synthesis_search_space":report["program_synthesis"]["search_space"],
        "report_sha256":report["report_sha256"],
    },indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
