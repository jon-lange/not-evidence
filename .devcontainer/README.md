# Devcontainer

Python 3.12 and nothing else. `make test` and `make demo` run on the standard library — no
dependencies, no network, no API keys.

The live probes need `openai` and `anthropic` and credentials at `~/.config/{openai,anthropic}-key`.
Those are per-specimen and cost money; install them inside the specimen you want to run:

```bash
cd specimens/<name>
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
```

The forbidden-token scanner needs the private config at `~/.config/re-denylist.toml`, which is
deliberately outside every git tree and therefore not present in a fresh container. `pre-commit` will
refuse rather than skip — that is intended. A scan that silently passes because its config is missing
is the failure mode this repository is named after.
