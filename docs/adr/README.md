# Architecture Decision Records

An ADR captures a decision that was expensive to make and would be expensive to
reverse: why we picked an approach, what we rejected, and what we accepted as a
consequence. It is not documentation of how the code works — that belongs in
[`docs/architecture.md`](../architecture.md) and in the code itself.

Write an ADR when a change:

- picks one tool/approach where several were plausible,
- constrains how future work has to be done,
- accepts a known trade-off or a known risk on purpose, or
- would otherwise make a future reader ask "why on earth is it like this?"

Do **not** write one for routine changes, bug fixes, or anything a commit
message already explains.

## Index

| ADR | Title | Status |
|---|---|---|
| [0001](0001-tiered-load-testing-harness.md) | Tiered load-testing harness (k6 + isolated Compose stack + OSRM stub) | Proposed |

## Statuses

| Status | Meaning |
|---|---|
| **Proposed** | Open for comment. The decision is being made *now*; disagreement is cheap at this stage. |
| **Accepted** | Merged and in force. Still amendable, but changing it means a new ADR. |
| **Superseded** | Replaced by a later ADR. Keep the file; add a link to the replacement at the top. |
| **Deprecated** | No longer applies, and nothing replaced it (e.g. the subsystem was removed). |

Never delete or silently rewrite an accepted ADR. The record of a decision that
turned out badly is more valuable than the absence of it.

## How to comment on a Proposed ADR

1. **On the pull request that introduces it** — this is the preferred path
   while the ADR is still `Proposed`. Use inline review comments on the
   specific paragraph you disagree with.
2. **In a follow-up PR** — if the ADR is already merged, open a PR that either
   amends the "Open questions" section or adds a new ADR that supersedes it.

Every ADR ends with an **Open questions / call for comments** section. Those
are the points the author is genuinely unsure about and actively wants pushback
on — start there.

## Writing a new one

Copy the structure of an existing ADR. Number sequentially, zero-padded to four
digits, with a kebab-case slug: `0002-some-decision.md`. Keep it in English to
match the rest of `docs/`.

Two rules worth stating explicitly, because they are what makes ADRs worth
reading years later:

- **Record the rejected options, not just the chosen one.** An ADR that only
  says what we did is a changelog entry.
- **Be honest about what you did not verify.** "We assumed X and did not test
  it" is a genuinely useful sentence.
