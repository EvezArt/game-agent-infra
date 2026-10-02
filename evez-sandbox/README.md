# EVEZ Sandbox

A browser-native prototype for the EVEZ agentic sandbox: every session is a fresh procedural society, while agents inhabit the simulation rather than merely completing tasks.

## Core law

**WORLD > AGENT.** Agents are inhabitants with roles, needs, relationships, institutions, tools, memory, evidence, and consequences.

The runtime exposes six loops:

1. world generation
2. embodied agent life
3. society/economy
4. evidence and uncertainty
5. tool/knowledge invention
6. player intervention

This prototype is deliberately dependency-free. Open `index.html` directly on a phone or serve the directory with any static HTTP server.

The browser shell is the game surface. A future bridge can connect the same protocol to OpenClaw/Hermes-class runtimes, authenticated web browsing, user data connectors, and external model providers.

## Reality boundary

The prototype never pretends that a simulated action happened on the real internet. Real-world tools must enter through explicit bridge capabilities and produce provenance records.

## Next bridge

`bridge-protocol.md` defines the capability contract for:

- web navigation
- authenticated user-authorized data
- GitHub
- files
- calendars/mail
- external APIs
- model inference
- persistent event ledger

No Replit dependency.
