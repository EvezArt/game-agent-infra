#!/usr/bin/env python3
"""
CARET structural invariance battery.

The useful question is not merely "what does this glyph mean?"
It is "which properties remain invariant when we transform the diagram?"

Tests:
  - rotation orbit
  - reflection orbit
  - uniform scale
  - translation
  - symbol permutation
  - relation-preserving permutation

Outputs:
  canonical orbit signature
  invariant fields
  sensitivity fields
  collision warnings

No physical or extraterrestrial inference is made.
"""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from typing import Any

def load_interpreter():
    import importlib.util, sys
    p=Path(__file__).resolve().with_name("caret_lap_interpreter.py")
    spec=importlib.util.spec_from_file_location("caret_lap_interpreter",p)
    m=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=m
    assert spec.loader
    spec.loader.exec_module(m)
    return m

def transform(doc, *, theta=0.0, reflect_x=False, scale=1.0, dx=0.0, dy=0.0, permute=False):
    c,s=math.cos(theta),math.sin(theta)
    out={"signature_depth":doc.get("signature_depth",6),"symbols":[]}
    symbols=list(doc.get("symbols",[]))
    if permute:
        symbols=list(reversed(symbols))
    for sym in symbols:
        ns={"id":sym["id"],"primitives":[]}
        for p in sym.get("primitives",[]):
            q=dict(p)
            pts=q.get("points")
            if pts is not None:
                new=[]
                for x,y in pts:
                    x=float(x)*scale
                    y=float(y)*scale
                    if reflect_x:
                        y=-y
                    xr=c*x-s*y+dx
                    yr=s*x+c*y+dy
                    new.append([xr,yr])
                q["points"]=new
            if "cx" in q and "cy" in q:
                x=float(q["cx"])*scale
                y=float(q["cy"])*scale
                if reflect_x:
                    y=-y
                q["cx"]=c*x-s*y+dx
                q["cy"]=s*x+c*y+dy
            if "r" in q:
                q["r"]=float(q["r"])*abs(scale)
            if "start" in q:
                q["start"]=float(q["start"])+(math.degrees(theta) if not reflect_x else -math.degrees(theta))
            if "end" in q:
                q["end"]=float(q["end"])+(math.degrees(theta) if not reflect_x else -math.degrees(theta))
            ns["primitives"].append(q)
        out["symbols"].append(ns)
    return out

def structural_key(result: dict[str,Any]):
    return {
        "relations":[
            [e["relation"], round(float(e.get("distance",0.0)),6)]
            for e in sorted(result["relations"], key=lambda x:(x["relation"],x["source"],x["target"]))
        ],
        "morphologies":[
            {
                "id":n["id"],
                "primitive_count":n["descriptor"]["primitive_count"],
                "morphology":n["descriptor"]["morphology"],
                "aspect_ratio":n["descriptor"]["aspect_ratio"],
            }
            for n in sorted(result["symbols"],key=lambda x:x["id"])
        ],
    }

def h(x):
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def run(doc):
    m=load_interpreter()
    base=m.build(doc)
    variants={
        "identity":doc,
        "rot_45":transform(doc,theta=math.pi/4),
        "rot_90":transform(doc,theta=math.pi/2),
        "rot_180":transform(doc,theta=math.pi),
        "reflect_x":transform(doc,reflect_x=True),
        "scale_2":transform(doc,scale=2.0),
        "translate":transform(doc,dx=137.0,dy=-71.0),
        "rot_reflect":transform(doc,theta=math.pi/3,reflect_x=True),
        "reverse_symbols":transform(doc,permute=True),
    }
    reports={}
    for name,d in variants.items():
        r=m.build(d)
        reports[name]={
            "recursive_signature":r["recursive_signature"]["signature"],
            "result_sha256":r["result_sha256"],
            "structural_key":structural_key(r),
            "structural_key_sha256":h(structural_key(r)),
        }
    basekey=reports["identity"]["structural_key_sha256"]
    invariants=[]
    sensitivities=[]
    for name,v in reports.items():
        if v["structural_key_sha256"]==basekey:
            invariants.append(name)
        else:
            sensitivities.append(name)
    return {
        "engine":"EVEZ-CARET-Invariance-Battery",
        "evidence_status":"PROPOSED",
        "invariant_variants":invariants,
        "sensitive_variants":sensitivities,
        "reports":reports,
        "interpretation":{
            "invariant": "candidate structural feature survives this transformation",
            "sensitive": "candidate structural feature changes under this transformation",
            "warning": "A changed hash does not imply semantic change; a matching hash does not prove semantic equivalence."
        }
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o","--output")
    a=ap.parse_args()
    doc=json.loads(Path(a.input).read_text())
    result=run(doc)
    result["result_sha256"]=h(result)
    text=json.dumps(result,indent=2)+"\n"
    if a.output: Path(a.output).write_text(text)
    else: print(text,end="")

if __name__=="__main__":
    main()
