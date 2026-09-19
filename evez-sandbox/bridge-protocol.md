# EVEZ Bridge Protocol v0.1

The game is the simulation. Bridges are capabilities.

## Envelope

Every tool invocation is an immutable event:

```json
{
  "event_id": "evt-...",
  "session_id": "world-...",
  "actor_id": "agent-...",
  "capability": "web.navigate",
  "intent": "inspect_public_page",
  "input": {},
  "authorization": "player",
  "result": {},
  "evidence": [],
  "timestamp": "...",
  "prev_hash": "...",
  "hash": "..."
}
```

## Capability classes

### web.navigate
Open a public URL, inspect rendered content, follow links, type into forms when permitted, capture page state, and return provenance. Authentication is never silently inferred.

### data.read
Read user-authorized connected data. Each source has a declared scope and freshness timestamp.

### data.write
Write only after an explicit authorization policy allows the operation. Financial transfers, destructive actions, account security changes, and external publication remain gated.

### agent.spawn
Create an inhabitant with lineage, role, skills, constraints, memory seed, and starting social context.

### tool.forge
Create a simulated tool from an agent proposal. The simulator tests preconditions, costs, failure modes, and observed outcomes before admitting it to the world.

### institution.forge
Create or mutate a guild, company, government, school, cult, laboratory, market, family, or other social institution. Institutions have constitutions, resources, roles, norms, and internal conflicts.

### evidence.observe
Record observation separately from interpretation. Evidence may be VERIFIED, INFERRED, UNKNOWN, STALE, or CONTRADICTED.

### world.branch
Fork a world state without rewriting the parent history.

## Anti-hallucination rule

A simulated fact and a real-world fact are different types. Never merge them. Every external observation must carry a source, retrieval time, and capability invocation.

## Agent loop

PERCEIVE -> ORIENT -> NEED -> PLAN -> ACT -> OBSERVE CONSEQUENCE -> UPDATE BELIEF -> NEGOTIATE -> LEARN

Agents may refuse a plan, misunderstand it, invent a better one, change occupation, form relationships, leave institutions, teach others, and create new objectives.

## Society loop

HOUSEHOLDS -> LABOR -> PRODUCTION -> TRADE -> INSTITUTIONS -> LAW/NORMS -> CONFLICT/COOPERATION -> CULTURE -> NEXT GENERATION

No quest generator is required.
