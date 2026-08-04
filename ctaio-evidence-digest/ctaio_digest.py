#!/usr/bin/env python3
"""A small, auditable multi-agent publishing pipeline for ctaio.dev.

Run the deterministic demo:
    python3 ctaio_digest.py --demo

Run with Claude:
    ANTHROPIC_API_KEY=... python3 ctaio_digest.py --input sources.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class Source:
    title: str
    url: str
    text: str


class ClaudeClient:
    """Tiny HTTP client so the workflow has no runtime dependencies."""

    def __init__(self, model: str = "claude-sonnet-4-5") -> None:
        self.api_key = os.environ["ANTHROPIC_API_KEY"]
        self.model = model

    def __call__(self, system: str, prompt: str) -> str:
        body = json.dumps({
            "model": self.model,
            "max_tokens": 1800,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "content-type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=60) as response:
            payload = json.load(response)
        return "\n".join(block["text"] for block in payload["content"] if block["type"] == "text")


def evidence_packet(sources: list[Source]) -> str:
    return "\n\n".join(
        f"[S{i}] {s.title}\nURL: {s.url}\nEXCERPT: {s.text[:2400]}"
        for i, s in enumerate(sources, 1)
    )


def researcher_agent(call_llm: Callable[[str, str], str], sources: list[Source]) -> str:
    return call_llm(
        "You are the ctaio.dev research agent. Prefer concrete workflow details over hype.",
        "Create a practitioner brief with 3 findings. Every factual claim must end in [S#]. "
        "Include one reproducible experiment and one skeptical caveat. Use only this evidence:\n\n"
        + evidence_packet(sources),
    )


def verifier_agent(call_llm: Callable[[str, str], str], draft: str, sources: list[Source]) -> str:
    allowed = {f"S{i}" for i in range(1, len(sources) + 1)}
    used = set(re.findall(r"\[(S\d+)\]", draft))
    if not used or not used <= allowed:
        raise ValueError(f"citation gate failed: used={sorted(used)}, allowed={sorted(allowed)}")
    return call_llm(
        "You are a strict fact-checking editor. Delete unsupported claims; never manufacture citations.",
        "Return a corrected Markdown brief. Preserve valid [S#] citations. End with a 'Verification' "
        "section listing PASS/FAIL for citation coverage, reproducibility, and hype.\n\n"
        f"DRAFT:\n{draft}\n\nEVIDENCE:\n{evidence_packet(sources)}",
    )


def publisher_agent(call_llm: Callable[[str, str], str], verified: str, sources: list[Source]) -> str:
    source_list = "\n".join(f"- [S{i}] [{s.title}]({s.url})" for i, s in enumerate(sources, 1))
    result = call_llm(
        "You publish ctaio.dev: senior-engineer voice, compact, specific, and low-hype.",
        "Format this as a publishable weekly field note with title, 2-sentence dek, findings, "
        "experiment, caveat, and source list. Do not remove [S#] markers.\n\n" + verified,
    )
    return result.rstrip() + "\n\n## Sources\n" + source_list + "\n"


def demo_llm(system: str, prompt: str) -> str:
    """Deterministic offline adapter that exercises the same handoffs and gates."""
    if "research agent" in system:
        return (
            "## Findings\n"
            "1. Agent workflows should expose tool calls as inspectable events [S1].\n"
            "2. Small evaluation cases catch regressions before broad rollout [S2].\n"
            "3. Human review belongs at irreversible boundaries, not every step [S1].\n\n"
            "## Experiment\nRun the supplied task twice, record every tool call, then diff outputs [S2].\n\n"
            "## Caveat\nA clean demo trace does not prove production reliability [S1]."
        )
    if "fact-checking editor" in system:
        draft = prompt.split("DRAFT:\n", 1)[1].split("\n\nEVIDENCE:", 1)[0]
        return draft + "\n\n## Verification\n- Citation coverage: PASS\n- Reproducibility: PASS\n- Hype: PASS"
    return "# Agent Workflows Need Receipts\n\nA compact field note for engineers.\n\n" + prompt.split("\n\n", 1)[1]


def load_sources(path: str | None, demo: bool) -> list[Source]:
    if demo:
        return [
            Source("Observable agent runs", "https://ctaio.dev/notes/observable-runs", "Record tool inputs, outputs, latency, and approval boundaries."),
            Source("Evaluation before rollout", "https://ctaio.dev/notes/evals", "Keep a small fixed evaluation set and compare every workflow change."),
        ]
    rows = json.loads(Path(path or "sources.json").read_text())
    return [Source(**row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input")
    parser.add_argument("--output", default="digest.md")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    sources = load_sources(args.input, args.demo)
    llm = demo_llm if args.demo else ClaudeClient()
    researched = researcher_agent(llm, sources)
    verified = verifier_agent(llm, researched, sources)
    published = publisher_agent(llm, verified, sources)
    Path(args.output).write_text(published)
    print(f"published {args.output} from {len(sources)} sources")


if __name__ == "__main__":
    main()
