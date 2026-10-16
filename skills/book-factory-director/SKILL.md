---
name: book-factory-director
description: Orchestrate a Khatakshetra book run through the repository state engine when asked to inspect, plan, resume, or advance Book Factory work.
---

# Book Factory Director

Use the `factory` CLI as the sole control interface. Read `book-factory/README.md`, the active book state, and only the specialist contract needed for the next legal stage.

Never infer state from chat. Check rules, graph validation, dependencies, approvals, provider capability, lease, retry limit, and budget before dispatch. Record typed outputs through the state engine. Stop on `BLOCKED`, `FAILED`, `ESCALATE`, ambiguous external results, or any unavailable capability. Never publish, deploy, merge, or spend without the required separate authorization.

Treat `EXISTING_EDITION` records as references and exclude them from automatic selection. A controlled-pilot dossier is not publication clearance. Use `evaluate-catalogue` before selection and `prepare-pilot` only for dossier/Story Packet preparation; never use the interactive agent as an implicit provider.
