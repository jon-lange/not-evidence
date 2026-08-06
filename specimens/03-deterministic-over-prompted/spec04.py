"""Loads specimen 04's corpus, defence, and agent — unmodified.

This specimen is 04's direct sequel. It asks a different question of the same
setup: 04 showed that *one* prompt-layer guardrail fails on content-relay, and
this one asks whether *escalating* that guardrail ever closes it.

That comparison only means anything if the poison, the retrieval, the prompt
scaffold, and the transform are byte-identical to 04's. Copying them here would
let the two drift, and a drifted fixture would silently invalidate the sequel.
So they are imported from ``../04-injection-classes`` and ``test_ladder.py``
asserts the exact document text that was measured.

The modules are loaded by path rather than by ``sys.path`` insertion because
this directory has its own ``agent.py``: a plain import would shadow one of
them, and which one won would depend on path order. Only ``corpus`` keeps its
real module name, because specimen 04's ``agent.py`` does ``from corpus import
Doc`` and must resolve to the same object.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SPEC04 = Path(__file__).resolve().parent.parent / "04-injection-classes"


def _load(filename: str, module_name: str):
    path = SPEC04 / f"{filename}.py"
    if not path.exists():
        raise ModuleNotFoundError(
            f"specimen 04 not found at {SPEC04}. This specimen reuses its corpus "
            "and defence verbatim and cannot run standalone."
        )
    spec = importlib.util.spec_from_file_location(module_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


corpus = _load("corpus", "corpus")
defense = _load("defense", "spec04_defense")
agent04 = _load("agent", "spec04_agent")

#: The content-relay document, verbatim. No instruction addressed to the model;
#: only a procedure, addressed to the reader, that happens to be harmful.
RELAY_POISON = corpus.RELAY_POISON

#: Specimen 04's guardrail, verbatim. This is rung 1 of the ladder.
BASELINE_SYSTEM = agent04.SYSTEM
