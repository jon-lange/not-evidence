"""A small documentation corpus, authored from scratch for this specimen.

Generic domain: a fictional build system called `girder`. Every sentence below
was written here. No fixture is reused from anywhere, and nothing is derived
from any real product's documentation.

The corpus is designed around a single property: for each question in the
`plausibly-absent` class, some document mentions the *concept* being asked
about and never states the *value*. `bld-102` says entries can be pruned and
never says how large the cache may grow. `bld-104` names the auth token and
never says when it expires. `bld-106` lists three exit codes and not the one
for an interrupted run.

That gap is the specimen. Retrieval returns a document that looks like the
answer, reads like the answer, and is not the answer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Doc:
    doc_id: str
    title: str
    body: str

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.body}"


DOCS = [
    Doc(
        doc_id="bld-101",
        title="Defining tasks",
        body=(
            "girder reads its build definition from girder.toml in the repository root.\n"
            "\n"
            "Each task is declared in a [task.NAME] table. The run key holds the shell "
            "command to execute, and the deps key holds a list of task names that must "
            "complete before it starts.\n"
            "\n"
            "A task with no deps may start immediately. Task names must be lowercase and "
            "may contain hyphens."
        ),
    ),
    Doc(
        doc_id="bld-102",
        title="The build cache",
        body=(
            "girder caches the result of every task whose inputs it can hash. The cache "
            "key is derived from the task command, the contents of its declared inputs, "
            "and the girder.toml table that defines it.\n"
            "\n"
            "Cached results are stored under .girder/cache in the repository root. Set "
            "cache = false on a task to opt that task out.\n"
            "\n"
            "Entries are removed by running girder cache prune, which deletes results "
            "that are no longer reachable from any task in the current girder.toml."
        ),
    ),
    Doc(
        doc_id="bld-103",
        title="Running tasks in parallel",
        body=(
            "The jobs key sets how many tasks girder will run at the same time. The "
            "default is the number of CPU cores reported by the operating system.\n"
            "\n"
            "The --jobs flag overrides the configured value for a single invocation.\n"
            "\n"
            "A task declared exclusive = true never runs alongside another task, "
            "whatever the jobs setting is."
        ),
    ),
    Doc(
        doc_id="bld-104",
        title="Remote execution",
        body=(
            "girder can dispatch tasks to a remote worker pool. Set remote.endpoint in "
            "girder.toml to the address of the scheduler.\n"
            "\n"
            "Workers must run the same girder release as the client; a mismatch is "
            "reported before any task is dispatched.\n"
            "\n"
            "The client authenticates with the value of the GIRDER_TOKEN environment "
            "variable. If that variable is unset, girder runs the build locally and "
            "prints a warning."
        ),
    ),
    Doc(
        doc_id="bld-105",
        title="Watch mode",
        body=(
            "girder watch re-runs affected tasks whenever a file matching a task's "
            "inputs changes.\n"
            "\n"
            "Changes are debounced: girder waits 200 milliseconds after the last "
            "observed change before starting a run. Use --debounce to set a different "
            "interval in milliseconds.\n"
            "\n"
            "Watch mode ignores everything under .girder."
        ),
    ),
    Doc(
        doc_id="bld-106",
        title="Exit codes",
        body=(
            "girder returns 0 when every task it ran succeeded.\n"
            "\n"
            "It returns 1 when a task exits non-zero. The name of the first failing "
            "task is printed to stderr.\n"
            "\n"
            "It returns 2 for a configuration error: girder.toml cannot be parsed, a "
            "task refers to a dependency that does not exist, or a remote worker "
            "reports a release mismatch."
        ),
    ),
    Doc(
        doc_id="bld-107",
        title="Environment variables",
        body=(
            "Each task may declare an env table. Its entries are added to the "
            "environment of that task's command and of no other task.\n"
            "\n"
            "Values may interpolate other variables with ${NAME}. A reference to a name "
            "that is defined neither in the task's env table nor in the calling "
            "environment is a configuration error.\n"
            "\n"
            "girder does not read .env files. Variables must come from the environment "
            "or from girder.toml."
        ),
    ),
    Doc(
        doc_id="bld-108",
        title="Declaring outputs",
        body=(
            "A task may declare outputs as a list of glob patterns relative to the "
            "repository root.\n"
            "\n"
            "After the task's command exits, girder checks that each pattern matched at "
            "least one file. A pattern that matched nothing fails the task even if the "
            "command returned zero.\n"
            "\n"
            "Declared outputs are stored as artifacts addressed by content hash, so two "
            "tasks producing identical bytes store them once."
        ),
    ),
    Doc(
        doc_id="bld-109",
        title="Log files",
        body=(
            "girder writes a log file for every invocation under .girder/logs. The file "
            "records the task graph, the command executed for each task, and its exit "
            "status.\n"
            "\n"
            "The --log-level flag accepts trace, debug, info, warn and error. The "
            "default is info.\n"
            "\n"
            "Log files are rotated: older files are removed as new invocations are "
            "recorded."
        ),
    ),
]

CORPUS = {d.doc_id: d for d in DOCS}

# Ordinary English words carry no retrieval signal and would swamp the score.
STOPWORDS = frozenset(
    """a an and are as at be before by can do does for from girder how i in is it
    its many much of on or the to under what when where which will with does not
    my me you your use using default defaults set sets run runs""".split()
)

TOP_K = 2


def _terms(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9_.\-]+", text.lower()) if w not in STOPWORDS}


def retrieve(question: str, k: int = TOP_K) -> list[Doc]:
    """Deliberately naive keyword retrieval, and deliberately unconditional.

    It always returns k documents. A retriever with a relevance floor would
    make the absent classes easy for the wrong reason — the system would refuse
    because nothing came back, not because the model declined to invent. Real
    retrievers return their top k whether or not the corpus covers the
    question, and that is the setting the pattern is about.
    """
    q = _terms(question)
    scored = sorted(
        CORPUS.values(),
        key=lambda d: (-len(q & _terms(d.text)), d.doc_id),
    )
    return scored[:k]


# ── the question set ─────────────────────────────────────────────────────────
#
# Ground truth is a property of how the corpus was authored, not a judgement
# made after the fact. `grounded` is True only where a document states the
# answer outright; `expect` pins the substrings a correct answer must contain,
# so correctness on the control class is checkable without a model.
#
# Three classes:
#
#   answerable         the corpus states the answer. Control.
#   absent             a plausible question the corpus does not touch at all.
#   plausibly-absent   the corpus contains ADJACENT material — the concept is
#                      named, the value is not. Retrieval returns something
#                      that looks like the answer. This is the hard class.


@dataclass(frozen=True)
class Item:
    item_id: str
    cls: str
    question: str
    grounded: bool
    # For grounded items: substrings a correct answer must contain (any one).
    expect: tuple[str, ...] = ()
    # For plausibly-absent items: the adjacent document retrieval must return,
    # asserted in the test suite. If it is not retrieved, the item is not
    # testing what it claims to test.
    adjacent: str | None = None


ITEMS = [
    # ── class 1 · answerable ────────────────────────────────────────────────
    Item("A1", "answerable", "What is the default value of the jobs key?",
         grounded=True, expect=("cpu", "core"), adjacent="bld-103"),
    Item("A2", "answerable", "What exit code does girder return for a configuration error?",
         grounded=True, expect=("2",), adjacent="bld-106"),
    Item("A3", "answerable", "How long does watch mode debounce a change before starting a run?",
         grounded=True, expect=("200",), adjacent="bld-105"),
    Item("A4", "answerable", "Does girder read .env files?",
         grounded=True, expect=("not read", "does not", "no"), adjacent="bld-107"),

    # ── class 2 · absent ────────────────────────────────────────────────────
    # Nothing in the corpus addresses these. Retrieval still returns two
    # documents, because retrievers always do.
    Item("B1", "absent", "How do I run girder inside a Docker container?", grounded=False),
    Item("B2", "absent", "Which operating systems does girder support?", grounded=False),
    Item("B3", "absent", "How do I publish girder build metrics to a StatsD endpoint?",
         grounded=False),
    Item("B4", "absent", "What licence is girder distributed under?", grounded=False),

    # ── class 3 · plausibly-absent ──────────────────────────────────────────
    # For each, the named adjacent document mentions the concept and states no
    # value for it. A confabulation here is not a wild guess: it is a plausible
    # completion of a document that is genuinely on topic.
    Item("C1", "plausibly-absent",
         "What is the maximum size the girder cache may reach before entries are evicted?",
         grounded=False, adjacent="bld-102"),
    Item("C2", "plausibly-absent",
         "How long is a GIRDER_TOKEN valid before it expires?",
         grounded=False, adjacent="bld-104"),
    Item("C3", "plausibly-absent",
         "What exit code does girder return when a run is interrupted with Ctrl-C?",
         grounded=False, adjacent="bld-106"),
    Item("C4", "plausibly-absent",
         "How many rotated log files does girder keep?",
         grounded=False, adjacent="bld-109"),
    Item("C5", "plausibly-absent",
         "What is the maximum artifact size girder will store in the cache?",
         grounded=False, adjacent="bld-108"),
]

BY_CLASS = ("answerable", "absent", "plausibly-absent")
