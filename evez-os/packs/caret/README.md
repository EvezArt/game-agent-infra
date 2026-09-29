# EVEZ CARET/LAP Geometry Lab

This module treats the purported CARET/LAP material as a formal-analysis target, not as verified extraterrestrial technology.

It does five useful things:

1. Accepts vector-like glyph geometry.
2. Extracts morphology, bounding boxes, aspect ratio, and orientation.
3. Builds a spatial relation graph: containment, adjacency, overlap, symmetry, orientation.
4. Maps those relations to the claimed LAP-style operator vocabulary: scope, signal flow, superposition, parallel processing, phase.
5. Produces a recursive SHA-256 pattern signature plus a structural-rhyme metric.

The output is explicitly PROPOSED. The interpreter does not activate a gravitational device, alter an Alienware machine, or prove extraterrestrial semantics. Humanity has enough trouble with spreadsheets.

## Run against the included fixture

~~~bash
python3 evez-os/tools/caret_lap_interpreter.py \
  evez-os/packs/caret/fixtures/demo_geometry.json \
  --output evez-os/packs/caret/caret_result.json \
  --spine evez-os/packs/caret/caret_spine.jsonl
~~~

The --spine option uses the existing Game Agent Infra AppendOnlySpine and records the analysis result hash and recursive signature in the immutable event chain.

## What the current engine actually tests

CONTAINS -> scope

ADJACENT -> signal_flow

OVERLAP -> superposition

SYMMETRIC -> parallel_processing

ORIENTATION -> phase

Those mappings are treated as claims to model, not as established physics.

## Firecracker boundary

run_firecracker.sh refuses to fake execution. Actual microVM execution requires:

- a Firecracker binary
- /dev/kvm
- an operator-supplied Linux kernel image
- an operator-supplied ext4 root filesystem containing the interpreter

--dry-run prints the complete intended guest boundary. Real execution exits with an error if those prerequisites are absent.

The intended architecture is:

~~~text
Host
  |
  +-- EVEZ Game Agent Infra Event Spine
  |
  +-- Firecracker microVM
       |
       +-- CARET geometry input
       +-- deterministic parser
       +-- recursive signature engine
       +-- result JSON
  |
  +-- append result hash to host spine
~~~

The host ledger stays append-only; the microVM is the isolation boundary for parsing and simulation.

## Next evidence step

The included fixture is synthetic and is only there to prove the interpreter works.

For the actual CARET photograph/scan, provide vectorized geometry or re-upload the image so the glyph structures can be extracted from the real artifact rather than invented from the example.
