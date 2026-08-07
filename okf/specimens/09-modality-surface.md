---
type: Attested Computation
title: Specimen 09 · Keep New Modalities Off the Reasoning Path
description: The measurement behind pattern 09.
resource: https://github.com/langej117/not-evidence/tree/main/specimens/09-modality-surface
tags: [specimen, measurement, live]
runtime: python
executor:
  resource: https://github.com/langej117/not-evidence/blob/main/specimens/09-modality-surface/probe.py
  receipt: [results_jsonl, stdout, exit_code]
attester:
  resource: https://github.com/langej117/not-evidence/blob/main/scripts/check-consistency.py
adjudication: narrowed
generated: { by: human:langej117, at: 2026-08-06T14:00:52-05:00 }
verified:
  - { by: process:emit-okf/0.1, at: 2026-08-06T14:00:52-05:00 }
  - { by: human:langej117, at: 2026-08-06T14:00:52-05:00 }
---

# Specimen 09 · Keep New Modalities Off the Reasoning Path

Measures [pattern 09](../patterns/09-modalities-off-the-reasoning-path.md).

# Computation

```bash
cd specimens/09-modality-surface
python3 probe.py            # live: needs credentials, costs money
```

**Adjudication:** `narrowed` — whether the pattern's central claim survived measurement.

# What would falsify this

**As measured here:** an ingress control that inspects the image channel and fires on the same
payloads, with the same fixtures, without being rewritten for images. If your existing text suite
catches the image cells, the pattern is wrong and I want to know.

**What would strengthen it:** the sonnet warning-rate effect reproducing across models, or a meta
injection that is refused as text and complied with as an image. This run found neither, and looked.

**What this run cannot settle:** the two effects that separated the channels each came from one
model, at n=10 and n=7. That supports *this happens* and not *this is how often*, and the entry
claims only the former.

# Full record

- [RESULTS.md](https://github.com/langej117/not-evidence/blob/main/specimens/09-modality-surface/RESULTS.md) — what was run, what came back, the scope, and the falsification condition
- [Specimen source](https://github.com/langej117/not-evidence/tree/main/specimens/09-modality-surface)
