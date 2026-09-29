#!/usr/bin/env python3
"""
Canonical CARET geometry signature.

Builds a dimensionless structural fingerprint intended to survive:
  - translation
  - rotation
  - reflection
  - uniform scale
  - symbol ordering

It deliberately discards absolute orientation and coordinates.
It keeps:
  morphology
  aspect ratios
  normalized pair distances
  relation labels

This is a geometry fingerprint, not a semantic decoder.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path

HERE=Path(__file__).resolve()
def interp():
    spec=importlib.util.spec_from_file_location("caret_lap_interpreter",HERE.with_name("caret_lap_interpreter.py"))
    m=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=m
    assert spec.loader
    spec.loader.exec_module(m)
    return m

def canonical(doc):
    m=interp()
    r=m.build(doc)
    nodes=sorted(r["symbols"],key=lambda n:n["id"])
    centers={}
    morph=[]
    for n in nodes:
        d=n["descriptor"]; b=d["bbox"]
        centers[n["id"]]=((b[0]+b[2])/2,(b[1]+b[3])/2)
        morph.append({
            "primitive_count":d["primitive_count"],
            "morphology":d["morphology"],
            "aspect_ratio":round(d["aspect_ratio"],6) if d["aspect_ratio"] is not None else None,
        })
    pairs=[]
    distances=[]
    for i,a in enumerate(nodes):
        for b in nodes[i+1:]:
            ax,ay=centers[a["id"]]; bx,by=centers[b["id"]]
            d=math.hypot(ax-bx,ay-by)
            distances.append(d)
            pairs.append((a["id"],b["id"],d))
    scale=math.sqrt(sum(d*d for d in distances)/len(distances)) if distances else 1.0
    nd=[]
    for a,b,d in pairs:
        nd.append([a,b,round(d/scale,6)])
    nd.sort()
    rels=sorted([e["relation"] for e in r["relations"]])
    payload={"nodes":morph,"normalized_pair_distances":nd,"relations":rels}
    return payload,hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    a=ap.parse_args()
    payload,sig=canonical(json.loads(Path(a.input).read_text()))
    print(json.dumps({"engine":"EVEZ-CARET-Canonical-Signature","signature":sig,
                      "evidence_status":"PROPOSED","fingerprint":payload},indent=2))

if __name__=="__main__":
    main()
