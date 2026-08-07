# Security

## What this repository is, in security terms

A catalogue of prose, plus twelve reference implementations and one standalone
tool. **Nothing here is maintained software and nothing here should be a
dependency.** The specimens exist to be read and run once; `tools/mutcheck.py`
exists to be copied.

There is no service, no deployed system, and no released package. So the
realistic security surface is narrow, and worth stating plainly rather than
implying something larger:

- **The specimens make outbound API calls** when you run their `probe.py` with
  credentials. They read keys from `~/.config/openai-key` and
  `~/.config/anthropic-key` or the matching environment variables, and never
  from inside this repository. If you find code here that writes a key to disk,
  reads one from the working tree, or sends one anywhere but the model endpoint,
  that is a real finding — report it.
- **The specimens contain deliberate attack payloads.** Prompt injections,
  poison documents, and adversarial fixtures are the subject matter. They are
  inert text and are meant to be read. They are not obfuscated and are not
  intended to be run against anything but the specimen's own harness.
- **`tools/mutcheck.py` swaps attributes on objects you pass it.** It is a test
  helper. Do not run it against production code paths.

## Reporting

**Use [private vulnerability reporting](https://github.com/jon-lange/not-evidence/security/advisories/new).**
That channel exists because [CONTRIBUTING.md](CONTRIBUTING.md) does not accept
pull requests — a fix cannot arrive the usual way, so the report needs somewhere
to go that is not a public issue.

Please include what you ran, what you expected, and what happened.

For anything that is **not** a security issue — a broken link, a wrong citation,
a result that contradicts a pattern — open an ordinary
[issue](https://github.com/jon-lange/not-evidence/issues). A contradicting
measurement is the most valuable thing anyone can send and is not a
vulnerability.

## What is in scope

- A key, token, or credential readable from anything in this repository.
- Code here that exfiltrates, logs, or transmits a secret.
- A specimen that damages or modifies anything outside its own directory.
- A workflow in `.github/` that could be made to execute untrusted input.

## What is not in scope

- **That the payloads work.** A prompt injection in `specimens/04-injection-classes/`
  successfully injecting a model is the measured result, not a vulnerability.
  Twelve entries here document things that fail; that is the point.
- **Dependency versions in a specimen's `requirements.txt`.** Specimens are
  unmaintained by design and pinned to what was installed when they were
  measured. Re-pinning them would invalidate the recorded results.
- **Anything about a model provider's service.** Report those to the provider.

## Expectations

This is a personal repository maintained by one person in their own time. I will
acknowledge a report, but I cannot commit to a response time, and there is no
bounty.

## What already runs

Described in full in [METHOD.md](METHOD.md), and enforced rather than promised:

- A public gitleaks ruleset and a private forbidden-token list, both over **full
  git history**, on every push and on demand. The private scan plants a canary
  and requires the scanner to catch it before a clean result is trusted.
- An identity audit over full history.
- GitHub secret scanning with push protection.
- Required status checks on `main`.
