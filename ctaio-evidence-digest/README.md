# ctaio.dev evidence-first digest workflow

A runnable three-agent pipeline tailored to ctaio.dev's senior engineering audience:

1. **Researcher** turns a bounded evidence packet into findings, a reproducible experiment, and a caveat.
2. **Verifier** enforces valid source markers before asking a separate fact-checking agent to remove unsupported claims.
3. **Publisher** applies ctaio.dev's compact, low-hype voice and appends an auditable source list.

The important handoff is structured evidence, not chat history. A deterministic offline adapter exercises the entire pipeline without an API key:

```bash
python3 ctaio_digest.py --demo --output digest.md
```

Production mode uses Claude through a dependency-free HTTP client:

```bash
export ANTHROPIC_API_KEY=...
python3 ctaio_digest.py --input sources.json --output digest.md
```

`sources.json` is an array of `{ "title", "url", "text" }` objects. In production I would add URL allowlisting, content hashes, per-step traces, retry budgets, and a human approval gate before publication.

## Failure intentionally handled

The first draft of the gate only checked whether *a* citation existed. That allowed unknown markers such as `[S99]` to pass. The corrected gate now verifies both presence and set membership against the exact evidence packet before the verifier or publisher can run.
