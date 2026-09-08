---
# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later
description: Code review, with the findings also rendered as readable prose
argument-hint: [low|medium|high|max] [PR number|branch|path] [--fix|--comment]
---

Run the `code-review` skill, passing it verbatim: $ARGUMENTS

The effort level, the scope and the verification passes stay the skill's
business. Only the reporting changes, at the end: report the verified findings
twice over.

First the `ReportFindings` call the skill asks for, unchanged — the host UI
reads it. Then, overriding the skill's rule against printing the findings as
text, write them out in the reply as well:

- Under headings by severity, worst first, numbered continuously across the
  headings.
- One entry per finding: the claim in bold, then a link to the exact spot —
  `[SKILL.md:37](.claude/skills/commit-message/SKILL.md#L37)`, relative to the
  repository root so the editor opens it.
- Below it, one or two sentences on the mechanism: what input reaches the code
  and what it does wrong. Never a paraphrase of the code the reader can see.
- A closing `→` line with the fix, whenever it fits in a sentence.
- Last, a short synthesis: which findings share one cause, and what to repair
  first.
- In the language the user is writing in.

When nothing survived verification, say so in one sentence and skip the
headings altogether.
