#!/usr/bin/env python3
"""
EVEZ CARET/LAP geometry interpreter.

Evidence-safe by construction: this parses and simulates symbolic geometry only.
It does not claim extraterrestrial provenance and does not actuate physical fields.

Input:
{
  "signature_depth": 6,
  "symbols": [
    {"id":"A","primitives":[
      {"kind":"circle","cx":0,"cy":0,"r":10},
      {"kind":"stroke","points":[[-10,0],[10,0]]}
    ]}
  ]
}
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

RELATIONS = {
    "CONTAINS": "scope",
    "CONTAINED_BY": "scope",
    "ADJACENT": "signal_flow",
    "OVERLAP": "superposition",
    "SYMMETRIC": "parallel_processing",
    "ORIENTATION": "phase",
}
KINDS = {"circle", "arc", "stroke", "spoke", "grid", "polygon", "point", "unknown"}


def sample_points(p: dict[str, Any]) -> list[tuple[float, float]]:
    kind = str(p.get("kind", "unknown")).lower()
    if kind == "circle" and all(k in p for k in ("cx", "cy", "r")):
        cx, cy, r = float(p["cx"]), float(p["cy"]), float(p["r"])
        return [(cx+r, cy), (cx, cy+r), (cx-r, cy), (cx, cy-r)]
    if kind == "arc" and all(k in p for k in ("cx", "cy", "r")):
        cx, cy, r = float(p["cx"]), float(p["cy"]), float(p["r"])
        a0 = math.radians(float(p.get("start", 0)))
        a1 = math.radians(float(p.get("end", 90)))
        return [(cx+r*math.cos(a0+(a1-a0)*i/12),
                 cy+r*math.sin(a0+(a1-a0)*i/12)) for i in range(13)]
    return [(float(x), float(y)) for x, y in p.get("points", [])]


def symbol_points(symbol: dict[str, Any]) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for p in symbol.get("primitives", []):
        pts.extend(sample_points(p))
    return pts


def descriptor(symbol: dict[str, Any]) -> dict[str, Any]:
    pts = symbol_points(symbol)
    kinds = {k: 0 for k in sorted(KINDS)}
    for p in symbol.get("primitives", []):
        k = str(p.get("kind", "unknown")).lower()
        kinds[k if k in kinds else "unknown"] += 1
    if not pts:
        return {"primitive_count": len(symbol.get("primitives", [])), "morphology": kinds,
                "bbox":[0,0,0,0], "aspect_ratio":None, "orientation_deg":0.0, "area_box":0.0}
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
    xx = sum((x-mx)**2 for x in xs)/len(xs)
    yy = sum((y-my)**2 for y in ys)/len(ys)
    xy = sum((x-mx)*(y-my) for x, y in pts)/len(pts)
    orientation = (math.degrees(0.5*math.atan2(2*xy, xx-yy)) % 180.0)
    return {
        "primitive_count": len(symbol.get("primitives", [])),
        "morphology": kinds,
        "bbox": [round(x0,6), round(y0,6), round(x1,6), round(y1,6)],
        "aspect_ratio": round((x1-x0)/(y1-y0), 6) if y1 != y0 else None,
        "orientation_deg": round(orientation, 6),
        "area_box": round(max(0.0,(x1-x0)*(y1-y0)), 6),
    }


def bbox_inter(a: list[float], b: list[float]) -> float:
    return max(0.0, min(a[2],b[2])-max(a[0],b[0])) * max(0.0, min(a[3],b[3])-max(a[1],b[1]))


def contains(a: list[float], b: list[float]) -> bool:
    return a[0] <= b[0] and a[1] <= b[1] and a[2] >= b[2] and a[3] >= b[3] and a != b


def center(d: dict[str, Any]) -> tuple[float,float]:
    b = d["bbox"]
    return ((b[0]+b[2])/2, (b[1]+b[3])/2)


def rels(a: dict[str, Any], b: dict[str, Any], da: dict[str, Any], db: dict[str, Any]) -> list[str]:
    out = []
    if contains(da["bbox"], db["bbox"]): out.append("CONTAINS")
    elif contains(db["bbox"], da["bbox"]): out.append("CONTAINED_BY")
    if bbox_inter(da["bbox"], db["bbox"]) > 0: out.append("OVERLAP")
    ax0, ay0, ax1, ay1 = da["bbox"]; bx0, by0, bx1, by1 = db["bbox"]
    gx, gy = max(bx0-ax1, ax0-bx1, 0), max(by0-ay1, ay0-by1, 0)
    scale = max(math.sqrt(max(da["area_box"]+db["area_box"],1)), 1)
    if math.hypot(gx,gy) <= 0.08*scale: out.append("ADJACENT")
    delta = abs(da["orientation_deg"]-db["orientation_deg"]) % 180
    delta = min(delta, 180-delta)
    if delta <= 1 or abs(delta-90) <= 1: out.append("ORIENTATION")
    if (da["morphology"] == db["morphology"] and
        da["aspect_ratio"] is not None and db["aspect_ratio"] is not None and
        abs(da["aspect_ratio"]-db["aspect_ratio"]) < 0.05):
        out.append("SYMMETRIC")
    return sorted(set(out))


def build(doc: dict[str, Any]) -> dict[str, Any]:
    symbols = sorted(doc.get("symbols", []), key=lambda s: str(s["id"]))
    if not symbols: raise ValueError("No symbols supplied")
    desc = {str(s["id"]): descriptor(s) for s in symbols}
    edges = []
    for i, a in enumerate(symbols):
        for b in symbols[i+1:]:
            da, db = desc[str(a["id"])], desc[str(b["id"])]
            ca, cb = center(da), center(db)
            distance = math.hypot(ca[0]-cb[0], ca[1]-cb[1])
            for r in rels(a,b,da,db):
                edges.append({"source":str(a["id"]), "target":str(b["id"]),
                              "relation":r, "operation":RELATIONS[r],
                              "distance":round(distance,6)})
    nodes = [{"id":str(s["id"]), "descriptor":desc[str(s["id"])]} for s in symbols]
    edge_core = [{k:e[k] for k in ("source","target","relation")}
                 for e in sorted(edges, key=lambda x:(x["source"],x["target"],x["relation"]))]
    current = {"nodes":nodes, "edges":edge_core}
    levels = [current]
    for level in range(int(doc.get("signature_depth",4))):
        packed = json.dumps(current, sort_keys=True, separators=(",",":")).encode()
        current = {"level":level+1, "parent":hashlib.sha256(packed).hexdigest(), "size":len(packed)}
        levels.append(current)
    signature = hashlib.sha256(json.dumps(levels[-1],sort_keys=True,separators=(",",":")).encode()).hexdigest()
    vectors = {}
    for sid,d in desc.items():
        vectors[sid] = [float(d["primitive_count"]), float(d["aspect_ratio"] or 0),
                        float(d["orientation_deg"]), float(sum(d["morphology"].values()))]
    rhyme=[]
    ids=sorted(vectors)
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            dist=math.sqrt(sum((x-y)**2 for x,y in zip(vectors[a],vectors[b])))
            rhyme.append({"a":a,"b":b,"distance":round(dist,6)})
    rhyme.sort(key=lambda x:x["distance"])
    result = {
        "engine":"EVEZ-CARET-LAP-Interpreter",
        "version":"0.1.0",
        "evidence_status":"PROPOSED",
        "physical_execution":False,
        "input_symbol_count":len(symbols),
        "symbols":nodes,
        "relations":edges,
        "claimed_operator_map":RELATIONS,
        "recursive_rhyme":{
            "definition":"Lower descriptor distance means stronger structural rhyme; this is a computational metric, not semantic equivalence.",
            "feature_vectors":vectors,
            "closest_pairs":rhyme[:10],
        },
        "recursive_signature":{"depth":int(doc.get("signature_depth",4)),
                               "signature":signature, "levels":levels},
        "falsification_hooks":[
            "Compare the same geometry under rotation and reflection.",
            "Require independent measurements before promoting any physical effect above PROPOSED.",
            "Blindly permute glyph order to test whether claimed semantics survive structure-preserving changes."
        ]
    }
    result["result_sha256"] = hashlib.sha256(
        json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return result


def append_spine(result: dict[str, Any], spine_path: Path, agent_id: str) -> str:
    repo = Path(__file__).resolve().parents[2]
    package_root = repo / "game-agent-infra"
    sys.path.insert(0, str(package_root))
    from game_agent_infra.core.spine import AppendOnlySpine
    spine = AppendOnlySpine(spine_path)
    ev = spine.append({
        "agent_id":agent_id,
        "anomaly":"caret_lap_analysis",
        "status":result["evidence_status"],
        "symbol_count":result["input_symbol_count"],
        "signature":result["recursive_signature"]["signature"],
        "result_sha256":result["result_sha256"],
        "timestamp_utc":time.time()
    })
    return ev.hash


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o","--output")
    ap.add_argument("--spine")
    ap.add_argument("--agent-id",default="caret-lap")
    args=ap.parse_args()
    result=build(json.loads(Path(args.input).read_text(encoding="utf-8")))
    if args.spine: result["spine_event_hash"]=append_spine(result,Path(args.spine),args.agent_id)
    text=json.dumps(result,indent=2,ensure_ascii=False)+"\n"
    if args.output: Path(args.output).write_text(text,encoding="utf-8")
    else: print(text,end="")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
