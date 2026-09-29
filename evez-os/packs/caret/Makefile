PYTHON ?= python3
INPUT ?= evez-os/packs/caret/fixtures/demo_geometry.json
OUT ?= evez-os/packs/caret/caret_result.json
SPINE ?= evez-os/packs/caret/caret_spine.jsonl

.PHONY: caret-test caret-demo caret-firecracker-dry

caret-test:
	$(PYTHON) -m pytest -q evez-os/packs/caret/tests

caret-demo:
	PYTHONPATH=game-agent-infra $(PYTHON) evez-os/tools/caret_lap_interpreter.py $(INPUT) --output $(OUT) --spine $(SPINE)

caret-firecracker-dry:
	sh evez-os/packs/caret/run_firecracker.sh --dry-run
