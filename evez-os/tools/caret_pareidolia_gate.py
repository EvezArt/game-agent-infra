#!/usr/bin/env python3
"""
CARET anti-pareidolia / null-model gate.

A small relational graph can look "meaningful" simply because there are few
ways to draw it. This gate asks whether a measured structural statistic
actually beats randomized null models.

Current statistics:
  - relation entropy
  - degree concentration
  - repeated-relation fraction
  - canonical signature compression ratio

The permutation p-value is empirical. It is not a probability that a glyph
system is alien; it only measures how surprising a statistic is under the
chosen null model.

Stdlib only.
"""
from __future__ import annotations
import argparse, hashlib, json, math, random
from pathlib import Path

def entropy(xs):
    n=len(xs)
    if n==0: return 0.0
    counts={}
    for x in xs: counts[x]=counts.get(x,0)+1
    return -sum((c/n)*math.log2(c/n) for c in counts.values())

def relation_stats(result):
    rels=[e["relation"] for e in result.get("relations",[])]
    deg={}
    for e in result.get("relations",[]):
        deg[e["source"]]=deg.get(e["source"],0)+1
        deg[e["target"]]=deg.get(e["target"],0)+1
    vals=list(deg.values())
    repeated=sum(c-1 for c in __import__("collections").Counter(rels).values() if c>1)
    return {
        "relation_entropy_bits":entropy(rels),
        "edge_count":len(rels),
        "node_count":len(result.get("symbols",[])),
        "max_degree":max(vals) if vals else 0,
        "degree_variance":(
            sum((x-(sum(vals)/len(vals)))**2 for x in vals)/len(vals)
            if vals else 0.0
        ),
        "repeated_relation_fraction":repeated/len(rels) if rels else 0.0,
    }

def shuffle_edges(result, rng):
    ids=[n["id"] for n in result.get("symbols",[])]
    rels=[e["relation"] for e in result.get("relations",[])]
    pairs=[]
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            pairs.append((a,b))
    rng.shuffle(pairs)
    chosen=pairs[:min(len(rels),len(pairs))]
    rng.shuffle(rels)
    out={
        "symbols":result.get("symbols",[]),
        "relations":[
            {"source":a,"target":b,"relation":r}
            for (a,b),r in zip(chosen,rels)
        ],
    }
    return out

def stat_vector(result):
    s=relation_stats(result)
    return (
        s["repeated_relation_fraction"],
        -s["relation_entropy_bits"],
        s["max_degree"],
        -s["degree_variance"],
    )

def score(result):
    v=stat_vector(result)
    # A compact scalar for empirical comparison. Larger is more structured.
    return v[0] + 0.1*v[1] + 0.01*v[2] + 0.001*v[3]

def run(result, permutations=2000, seed=1337):
    rng=random.Random(seed)
    observed=score(result)
    null=[]
    for _ in range(permutations):
        null.append(score(shuffle_edges(result,rng)))
    null.sort()
    exceed=sum(x>=observed for x in null)
    p=(exceed+1)/(len(null)+1)
    z=(observed-(sum(null)/len(null)))/(
        math.sqrt(sum((x-sum(null)/len(null))**2 for x in null)/len(null))
        or 1.0
    )
    return {
        "engine":"EVEZ-CARET-Pareidolia-Gate",
        "evidence_status":"PROPOSED",
        "seed":seed,
        "permutations":permutations,
        "observed_score":observed,
        "null_mean":sum(null)/len(null),
        "null_min":min(null) if null else None,
        "null_max":max(null) if null else None,
        "empirical_p_value":p,
        "null_z":z,
        "interpretation":{
            "small_p": "Observed statistic is unusual under this specific randomization model.",
            "large_p": "Observed statistic is not unusual under this specific randomization model.",
            "warning":"Neither outcome establishes semantics, authorship, extraterrestrial origin, or physical efficacy."
        }
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--permutations",type=int,default=2000)
    ap.add_argument("--seed",type=int,default=1337)
    a=ap.parse_args()
    report=json.loads(Path(a.input).read_text())
    if "relations" not in report:
        raise SystemExit("Input must be an interpreter result JSON containing relations")
    r=run(report,a.permutations,a.seed)
    r["result_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(json.dumps(r,indent=2))

if __name__=="__main__":
    main()
