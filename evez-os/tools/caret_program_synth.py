#!/usr/bin/env python3
"""
CARET/LAP program synthesizer.

Enumerates a finite gate vocabulary over the relation graph and searches for
high-information symbolic circuits. This is computational quantum simulation,
not a claim that the source material is extraterrestrial or physically quantum.

Search size:
  9 gate templates ^ 5 relation classes = 59,049 mappings.
For each mapping, the engine can scan eight rotations.

Stdlib only.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math
from pathlib import Path

from caret_quantum_speedrun import build_relations, run_circuit, rotate_primitives

REL_KEYS=("CONTAINS","ADJACENT","OVERLAP","SYMMETRIC","ORIENTATION")
GATES=("I","X","H","P90","P180","CP90","CP180","ENT90","ENT180")

def ops_for_mapping(parsed, mapping, n):
    out=[]
    ids=sorted(node["id"] for node in parsed["symbols"])
    qindex={sid:i % n for i,sid in enumerate(ids)}
    for e in parsed["relations"]:
        r=e["relation"]; src=e["source"]; tgt=e["target"]
        qa=qindex[src]; qb=qindex[tgt]; g=mapping[r]
        if g=="I": pass
        elif g=="X": out.append(("X",qa))
        elif g=="H": out.append(("H",qa))
        elif g=="P90": out.append(("PHASE",qa,math.pi/2))
        elif g=="P180": out.append(("PHASE",qa,math.pi))
        elif g=="CP90": out.append(("CPHASE",qa,qb,math.pi/2))
        elif g=="CP180": out.append(("CPHASE",qa,qb,math.pi))
        elif g=="ENT90":
            out.extend([("H",qa),("H",qb),("CPHASE",qa,qb,math.pi/2)])
        elif g=="ENT180":
            out.extend([("H",qa),("H",qb),("CPHASE",qa,qb,math.pi)])
    return out

def single_qubit_purity(state,n,q):
    r=[[0j,0j],[0j,0j]]
    for base in range(1<<(n-1)):
        low=base & ((1<<q)-1); high=base>>q
        i0=low | (high<<(q+1)); i1=i0 | (1<<q)
        a,b=state[i0],state[i1]
        r[0][0]+=a*a.conjugate(); r[1][1]+=b*b.conjugate()
        r[0][1]+=a*b.conjugate(); r[1][0]+=b*a.conjugate()
    return sum(abs(r[i][j])**2 for i in range(2) for j in range(2)).real

def run_and_score(doc,mapping,scan=False):
    parsed,_=build_relations(doc)
    n=max(1,min(4,len(parsed["symbols"])))
    docs=[rotate_primitives(doc,k*math.pi/4) for k in range(8)] if scan else [doc]
    ent=[]
    hashes=[]
    seen={}
    for d in docs:
        p,_=build_relations(d)
        ops=ops_for_mapping(p,mapping,n)
        key=hashlib.sha256(json.dumps(ops,separators=(",",":")).encode()).hexdigest()
        if key in seen:
            e=seen[key]
        else:
            st=run_circuit(n,ops)
            probs=[abs(x)**2 for x in st]
            e=-sum(x*math.log2(x) for x in probs if x>1e-15)
            seen[key]=e
        ent.append(e)
        hashes.append(key)
    mean=sum(ent)/len(ent)
    spread=math.sqrt(sum((x-mean)**2 for x in ent)/len(ent))
    return {"pre_score":mean-0.25*spread+0.001*len(set(hashes)),
            "mean_entropy_bits":mean,"entropy_spread":spread,"rotations":ent,"op_hashes":hashes}

def _entanglement(doc,mapping,scan):
    parsed,_=build_relations(doc)
    n=max(1,min(4,len(parsed["symbols"])))
    docs=[rotate_primitives(doc,k*math.pi/4) for k in range(8)] if scan else [doc]
    vals=[]
    for d in docs:
        p,_=build_relations(d)
        ops=ops_for_mapping(p,mapping,n)
        st=run_circuit(n,ops)
        purity=sum(single_qubit_purity(st,n,q) for q in range(n))/n
        vals.append(1.0-purity)
    return sum(vals)/len(vals)

def synth(doc, topk=12, scan=True):
    preliminary=[]
    for values in itertools.product(GATES, repeat=len(REL_KEYS)):
        mapping=dict(zip(REL_KEYS,values))
        pre=run_and_score(doc,mapping,scan=scan)
        preliminary.append({"mapping":mapping,**pre})
    preliminary.sort(key=lambda x:(-x["pre_score"],x["entropy_spread"],json.dumps(x["mapping"],sort_keys=True)))
    finalists=preliminary[:max(topk*16,128)]
    results=[]
    for item in finalists:
        entanglement=_entanglement(doc,item["mapping"],scan)
        score=item["pre_score"]+0.75*entanglement
        results.append({**item,
            "score":score,
            "mean_single_qubit_purity":1.0-entanglement,
            "entanglement_indicator":entanglement})
    results.sort(key=lambda x:(-x["score"],x["entropy_spread"],json.dumps(x["mapping"],sort_keys=True)))
    return {
        "engine":"EVEZ-CARET-Program-Synthesizer",
        "evidence_status":"PROPOSED",
        "mathematical_model":"exact finite-dimensional state-vector simulation",
        "search_space":f"{len(GATES)}^{len(REL_KEYS)}={len(GATES)**len(REL_KEYS)} mappings",
        "rotation_scan":bool(scan),
        "two_stage_search":True,
        "purity_evaluated_for":len(finalists),
        "topk":results[:topk],
        "disclaimer":"Generated circuits are candidate mathematical models of symbolic relations. Their ranking does not establish the meaning, origin, or physical efficacy of the source material."
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-k","--topk",type=int,default=12)
    ap.add_argument("--no-rotation-scan",action="store_true")
    ap.add_argument("-o","--output")
    a=ap.parse_args()
    doc=json.loads(Path(a.input).read_text())
    result=synth(doc,a.topk,not a.no_rotation_scan)
    result["result_sha256"]=hashlib.sha256(json.dumps(result,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    text=json.dumps(result,indent=2)+"\n"
    if a.output: Path(a.output).write_text(text)
    else: print(text,end="")

if __name__=="__main__":
    main()
