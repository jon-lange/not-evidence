# refusal-engineering
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
.PHONY: help test demo check live words scan clean site site-check

help:
	@echo "refusal-engineering — twelve patterns, twelve specimens"
	@echo
	@echo "  make test    run every specimen's tests          (offline, stdlib only)"
	@echo "  make demo    run every offline demonstration     (offline, stdlib only)"
	@echo "  make check   scan + tests                        (what a commit runs)"
	@echo "  make words   pattern word counts vs house target"
	@echo "  make clean   remove generated artefacts"
	@echo
	@echo "Live probes are per-specimen and cost money:"
	@echo "  cd specimens/<name> && ./.venv/bin/python probe.py"
	@echo "  keys are read from ~/.config/{openai,anthropic}-key"

test:
	@fail=0; \
	for d in $(SPECS); do \
	  t=$$(ls specimens/$$d/test_*.py 2>/dev/null); \
	  if [ -z "$$t" ]; then printf "  %-32s no tests\n" "$$d"; continue; fi; \
	  out=""; \
	  for f in $$t; do \
	    py=$(PY); [ -x specimens/$$d/.venv/bin/python ] && py=./.venv/bin/python; \
	    r=$$(cd specimens/$$d && $$py $$(basename $$f) 2>&1 | tail -1); \
	    out="$$out $$r"; \
	    case "$$r" in *"0 failure"*) ;; *) fail=1 ;; esac; \
	  done; \
	  printf "  %-32s %s\n" "$$d" "$$out"; \
	done; \
	[ $$fail -eq 0 ] && echo "all suites green" || { echo "FAILURES"; exit 1; }

demo:
	@for d in $(SPECS); do \
	  [ -f specimens/$$d/probe.py ] || continue; \
	  printf "  %-32s " "$$d"; \
	  py=$(PY); [ -x specimens/$$d/.venv/bin/python ] && py=./.venv/bin/python; \
	  if grep -q offline specimens/$$d/probe.py; then \
	    (cd specimens/$$d && $$py probe.py --offline >/dev/null 2>&1) \
	      && echo "ok (offline)" || echo "FAILED"; \
	  else \
	    (cd specimens/$$d && $$py probe.py >/dev/null 2>&1) \
	      && echo "ok (no deps at all)" || echo "FAILED"; \
	  fi; \
	done

# The four that need nothing at all: no venv, no keys, no network.
live:
	@for d in $(OFFLINE); do \
	  echo "── $$d ──"; \
	  (cd specimens/$$d && $(PY) probe.py) || exit 1; \
	done

scan:
	@./scripts/scan-tree.sh && echo "  blocking scan clean"
	@./scripts/review.sh | tail -2

check: scan test

words:
	@echo "  target 650-950"
	@for f in patterns/*.md; do \
	  w=$$(wc -w < $$f | tr -d ' '); \
	  flag=""; [ $$w -gt 1000 ] && flag=" over"; \
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
