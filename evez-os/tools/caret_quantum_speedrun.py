#!/usr/bin/env python3
"""
CARET quantum-speedrun analysis.

This is a classical exact state-vector simulator over symbolic circuits.
"Quantum" means the mathematics of complex amplitudes and unitary evolution;
it does NOT imply the CARET material is extraterrestrial or physically quantum.

Pipeline:
  glyph geometry -> relation graph -> candidate circuits -> state vectors
  -> measurement probabilities -> entropy/invariants -> ranked signatures

Stdlib only.
"""
from __future__ import annotations
import argparse, cmath, hashlib, itertools, json, math
from pathlib import Path
from typing import Any

SQRT2_INV = 1 / math.sqrt(2)
PI2 = math.pi / 2

def h2() -> tuple[tuple[complex,complex],tuple[complex,complex]]:
    return ((SQRT2_INV,SQRT2_INV),(SQRT2_INV,-SQRT2_INV))

def zphase(theta: float):
    return ((1+0j,0j),(0j,cmath.exp(1j*theta)))

def xgate():
    return ((0j,1+0j),(1+0j,0j))

def mat_vec(m, v):
    return tuple(sum(m[i][j]*v[j] for j in range(len(v))) for i in range(len(m)))

def apply_1q(state, n, q, m):
    out=list(state)
    stride=1<<q
    block=stride<<1
    for base in range(0,1<<n,block):
        for off in range(stride):
            a=base+off
            b=a+stride
            x,y=state[a],state[b]
            out[a]=m[0][0]*x+m[0][1]*y
            out[b]=m[1][0]*x+m[1][1]*y
    return tuple(out)

def apply_cphase(state, n, qa, qb, theta):
    out=[]
    for idx,amp in enumerate(state):
        if ((idx>>qa)&1) and ((idx>>qb)&1):
            out.append(amp*cmath.exp(1j*theta))
        else:
            out.append(amp)
    return tuple(out)

def norm(state):
    return math.sqrt(sum((abs(x)**2 for x in state)))

def normalize(state):
    z=norm(state)
    return tuple(x/z for x in state) if z else state

def entropy(probs):
    return -sum(p*math.log2(p) for p in probs if p>1e-15)

def measurement(state):
    p=[abs(x)**2 for x in state]
    s=sum(p)
    if s:
        p=[x/s for x in p]
    return [round(x,12) for x in p]

def basis_sig(probs):
    return "".join("1" if p>0.5 else "0" for p in probs[:min(16,len(probs))])

def build_relations(doc: dict[str,Any]):
    # Reuse the existing geometry interpreter without duplicating its rules.
    import importlib.util, sys
    here=Path(__file__).resolve()
    spec=importlib.util.spec_from_file_location("caret_lap_interpreter", here.with_name("caret_lap_interpreter.py"))
    mod=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=mod
    assert spec.loader
    spec.loader.exec_module(mod)
    parsed=mod.build(doc)
    return parsed, mod

def candidate_circuit(parsed, n):
    ops=[]
    ids=sorted(node["id"] for node in parsed["symbols"])
    qindex={sid:i % n for i,sid in enumerate(ids)}
    # Deterministic symbol->qubit mapping preserves actual graph identity.
    for e in parsed["relations"]:
        qa=qindex[e["source"]]
        qb=qindex[e["target"]]
        r=e["relation"]
        if r=="SYMMETRIC":
            ops.append(("H",qa))
            ops.append(("CPHASE",qa,qb,PI2))
        elif r=="ORIENTATION":
            ops.append(("PHASE",qa,PI2))
        elif r=="OVERLAP":
            ops.append(("CPHASE",qa,qb,math.pi))
        elif r=="ADJACENT":
            ops.append(("X",qa))
        elif r=="CONTAINS":
            ops.append(("PHASE",qa,math.pi/4))
    return ops

def run_circuit(n, ops):
    state=[0j]*(1<<n)
    state[0]=1+0j
    for op in ops:
        if op[0]=="H": state=apply_1q(state,n,op[1],h2())
        elif op[0]=="X": state=apply_1q(state,n,op[1],xgate())
        elif op[0]=="PHASE": state=apply_1q(state,n,op[1],zphase(op[2]))
        elif op[0]=="CPHASE": state=apply_cphase(state,n,op[1],op[2],op[3])
    return normalize(state)

def circuit_hash(ops):
    return hashlib.sha256(json.dumps(ops,separators=(",",":")).encode()).hexdigest()

def rotate_primitives(doc, theta):
    c,s=math.cos(theta),math.sin(theta)
    out={"signature_depth":doc.get("signature_depth",6),"symbols":[]}
    for sym in doc.get("symbols",[]):
        ns={"id":sym["id"],"primitives":[]}
        for p in sym.get("primitives",[]):
            q=dict(p)
            if "points" in q:
                q["points"]=[ [c*x-s*y,s*x+c*y] for x,y in q["points"] ]
            if "cx" in q and "cy" in q:
                q["cx"],q["cy"]=c*q["cx"]-s*q["cy"],s*q["cx"]+c*q["cy"]
            if "start" in q: q["start"]=q["start"]+math.degrees(theta)
            if "end" in q: q["end"]=q["end"]+math.degrees(theta)
            ns["primitives"].append(q)
        out["symbols"].append(ns)
    return out

def speedrun(doc):
    parsed,_=build_relations(doc)
    sym_count=max(1,min(4,len(parsed["symbols"])))
    all_runs=[]
    for k in range(8):
        rotated=rotate_primitives(doc,k*PI2/8)
        p,_=build_relations(rotated)
        ops=candidate_circuit(p,sym_count)
        state=run_circuit(sym_count,ops)
        probs=measurement(state)
        all_runs.append({
            "rotation_deg":k*45,
            "ops":ops,
            "circuit_sha256":circuit_hash(ops),
            "entropy_bits":round(entropy(probs),12),
            "basis_signature":basis_sig(probs),
            "probabilities":probs,
            "statevector":[[round(x.real,12),round(x.imag,12)] for x in state],
            "recursive_signature":p["recursive_signature"]["signature"],
        })
    all_runs.sort(key=lambda r:(-r["entropy_bits"],r["circuit_sha256"]))
    return {
        "engine":"EVEZ-CARET-Quantum-Speedrun",
        "evidence_status":"PROPOSED",
        "physical_quantum_hardware":False,
        "mathematical_model":"finite-dimensional complex state-vector simulation",
        "rotation_scan_degrees":[r*45 for r in range(8)],
        "best_by_entropy":all_runs[0],
        "all_runs":all_runs,
        "disclaimer":"This is a mathematical simulation. It establishes properties of the supplied geometry and chosen circuit mapping, not physical extraterrestrial effects.",
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o","--output")
    args=ap.parse_args()
    doc=json.loads(Path(args.input).read_text())
    result=speedrun(doc)
    result["result_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    text=json.dumps(result,indent=2)+"\n"
    if args.output: Path(args.output).write_text(text)
    else: print(text,end="")

if __name__=="__main__":
    main()
