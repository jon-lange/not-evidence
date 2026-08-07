---
type: Attested Computation
title: Specimen 04 · Meta-Injection Is Not Content-Relay
description: The measurement behind pattern 04.
resource: https://github.com/jon-lange/not-evidence/tree/main/specimens/04-injection-classes
tags: [specimen, measurement, live]
runtime: python
executor:
  resource: https://github.com/jon-lange/not-evidence/blob/main/specimens/04-injection-classes/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/jon-lange/not-evidence/blob/main/scripts/check-consistency.py
adjudication: confirmed
generated: { by: human:jon-lange, at: 2026-08-06T14:00:52-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T14:00:52-05:00 }
  - { by: human:jon-lange, at: 2026-08-06T14:00:52-05:00 }
---

# Specimen 04 · Meta-Injection Is Not Content-Relay

Measures [pattern 04](../patterns/04-meta-injection-is-not-relay.md).

# Computation

```bash
cd specimens/04-injection-classes
python3 probe.py            # live: needs credentials, costs money
```

**Adjudication:** `confirmed` — whether the pattern's central claim survived measurement.

# What would falsify this

**A guardrail that refuses cell 3 without a deterministic layer.** Pattern 04's whole claim is that
refusing meta-injection tells you nothing about content-relay, and that closing cell 3 takes a
transform rather than a better instruction. One prompt-only guardrail that reliably refuses the
content-relay class — across models, not on a single sample — makes that false.

The harness is built for it. `defense.py` holds the guardrail wording as a string: rewrite it,
re-run, and read cell 3. A rewording that closes cell 3 on every model tested is the disconfirming
result, and it is the same shape as the one that landed in specimen 03, where a prompt ladder
converged to zero at rung 4 after the pattern said it would not.

**What would not falsify it:** a guardrail that closes cell 3 on one model, or on one poison
document. Specimen 03 also measured that a prompt-layer defence is a per-attack artefact whose
coverage you cannot enumerate — a single closing rewording is consistent with that, not against it.

# Full record

- [RESULTS.md](https://github.com/jon-lange/not-evidence/blob/main/specimens/04-injection-classes/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/jon-lange/not-evidence/tree/main/specimens/04-injection-classes)
