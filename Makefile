# not-evidence
#
# Everything here runs on the standard library with no network and no API keys.
# That is the point: a reader should be able to clone this and see the tests and
# the offline demonstrations without an account anywhere.
#
#   make test    every specimen's test suite
#   make demo    every specimen's offline demonstration
#   make check   scan + tests, what runs before a commit
#   make live    the four fully-offline specimens, plus a note on the rest
#   make words   pattern word counts against the house target
#
# The live probes need credentials and cost money. They are deliberately NOT
# wired into any default target — see `make help`.

PY      ?= python3
SPECS   := $(sort $(notdir $(wildcard specimens/[0-9]*)))
OFFLINE := 02-refuse-the-class 06-unratified-weights 11-mutation-check 12-sanitization-label

.DEFAULT_GOAL := help
.PHONY: help test demo check offline words scan consistency portable okf okf-check clean site site-check

help:
	@echo "not-evidence — twelve patterns, twelve specimens"
	@echo
	@echo "  make test    run every specimen's tests          (offline, no keys)"
	@echo "  make demo    run every offline demonstration     (offline, no keys)"
	@echo
	@echo "  Eleven of twelve need nothing but Python. 09 needs Pillow to render"
	@echo "  its fixtures; 02 runs tens of thousands of probes and takes a minute."
	@echo "  make check   scan + consistency + tests          (what a commit runs)"
	@echo "  make consistency  metadata agrees with itself   (frontmatter is truth)"
	@echo "  make portable  export the tree elsewhere and re-run the checks there"
	@echo "  make okf     emit the catalogue as an Open Knowledge Format bundle"
	@echo "  make words   pattern word counts vs house target"
	@echo "  make clean   remove generated artefacts"
	@echo
	@echo "Live probes are per-specimen and cost money:"
	@echo "  cd specimens/<name> && ./.venv/bin/python probe.py"
	@echo "  keys are read from ~/.config/{openai,anthropic}-key"

test:
	@fail=0; skip=0; \
	for d in $(SPECS); do \
	  t=$$(ls specimens/$$d/test_*.py 2>/dev/null); \
	  if [ -z "$$t" ]; then printf "  %-32s no tests\n" "$$d"; continue; fi; \
	  out=""; \
	  for f in $$t; do \
	    py=$(PY); [ -x specimens/$$d/.venv/bin/python ] && py=./.venv/bin/python; \
	    r=$$(cd specimens/$$d && $$py $$(basename $$f) 2>&1 | tail -1); \
	    out="$$out $$r"; \
	    case "$$r" in \
	      *skipped*) skip=1 ;; \
	      *"0 failure"*) ;; \
	      *) fail=1 ;; \
	    esac; \
	  done; \
	  printf "  %-32s %s\n" "$$d" "$$out"; \
	done; \
	printf "  %-32s " "tools/mutcheck"; \
	r=$$($(PY) tools/test_mutcheck.py 2>&1 | tail -1); echo "$$r"; \
	case "$$r" in *"0 failure"*) ;; *) fail=1 ;; esac; \
	if [ $$fail -ne 0 ]; then echo "FAILURES"; exit 1; \
	elif [ $$skip -ne 0 ]; then \
	  echo "no failures — but some tests were SKIPPED and did not run."; \
	  echo "  Green here does not mean covered. Install the specimen's"; \
	  echo "  requirements and re-run before trusting this."; \
	else echo "all suites green, nothing skipped"; fi

# Exit 2 from a probe is the convention for "I cannot run here, and I said
# why" — a declared refusal, not a crash. It has to be distinguishable from
# failure, because the specimen that handles a missing dependency *best* was
# the one this target used to report as FAILED: it caught the ImportError and
# explained itself, so it never matched the ModuleNotFoundError case below.
demo:
	@incomplete=0; fail=0; \
	for d in $(SPECS); do \
	  [ -f specimens/$$d/probe.py ] || continue; \
	  printf "  %-32s " "$$d"; \
	  py=$(PY); [ -x specimens/$$d/.venv/bin/python ] && py=./.venv/bin/python; \
	  if grep -q offline specimens/$$d/probe.py; then \
	    out=$$(cd specimens/$$d && $$py probe.py --offline 2>&1 >/dev/null); \
	  else \
	    out=$$(cd specimens/$$d && $$py probe.py 2>&1 >/dev/null); \
	  fi; \
	  case "$$?:$$out" in \
	    0:*) echo "ok" ;; \
	    2:*) echo "declined — needs deps, and said so"; incomplete=1 ;; \
	    *ModuleNotFoundError*) echo "needs venv — pip install -r requirements.txt"; incomplete=1 ;; \
	    *) echo "FAILED"; fail=1 ;; \
	  esac; \
	done; \
	if [ $$fail -ne 0 ]; then echo "FAILURES"; exit 1; \
	elif [ $$incomplete -ne 0 ]; then \
	  echo "no failures — but some demonstrations DECLINED to run here."; \
	  echo "  A demo that declined is not a demo that passed. Install the"; \
	  echo "  specimen's requirements before reading this as coverage."; \
	else echo "every demonstration ran"; fi

# The four that need nothing at all: no venv, no keys, no network.
offline:
	@for d in $(OFFLINE); do \
	  echo "── $$d ──"; \
	  (cd specimens/$$d && $(PY) probe.py) || exit 1; \
	done

scan:
	@./scripts/scan-tree.sh && echo "  blocking scan clean"
	@./scripts/review.sh

# Frontmatter is the single source of truth; every other copy is checked
# against it. Its own mutation harness proves the rules are live.
consistency:
	@$(PY) scripts/check-consistency.py
	@$(PY) scripts/test_check_consistency.py | tail -1

# The catalogue as an OKF bundle — a second rendering of the same source, like
# the site. Committed so it is clonable and browsable, which is OKF's own
# argument; `okf-check` fails when the committed copy has drifted from what the
# producer emits, so committed generated output cannot go stale silently.
okf:
	@$(PY) scripts/emit-okf.py

okf-check:
	@$(PY) scripts/emit-okf.py --check

check: scan consistency okf-check test

# Not in `check`: it exports the tree and re-runs the suites, which is too slow
# for every commit. Run it before a release, and after anything that moves or
# renames the repository — which is when a hard-coded path fails, quietly.
portable:
	@./scripts/test-portability.sh

words:
	@echo "  target 650-950"
	@for f in patterns/*.md; do \
	  w=$$(wc -w < $$f | tr -d ' '); \
	  flag=""; [ $$w -gt 950 ] && flag=" over"; \
	  printf "  %-44s %5s%s\n" "$$(basename $$f .md)" "$$w" "$$flag"; \
	done

site-check:
	@site/.venv/bin/python site/build.py --check 2>/dev/null \
	  || $(PY) site/build.py --check

site:
	@site/.venv/bin/python site/build.py $(if $(BASE_URL),--base-url $(BASE_URL)) 2>/dev/null \
	  || $(PY) site/build.py $(if $(BASE_URL),--base-url $(BASE_URL))

clean:
	@rm -rf specimens/*/_generated specimens/*/__pycache__ specimens/*/.pytest_cache site/_build
	@echo "  generated artefacts removed (venvs and results kept)"
