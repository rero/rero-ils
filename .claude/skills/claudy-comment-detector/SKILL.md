---
# SPDX-FileCopyrightText: Ben Stolovitz (citelao), Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later
name: claudy-comment-detector
description: Detects comments that are "Claude-y", e.g. over-specific or refer to internal turns
---

# Claudy Comment Detector

## Description

AI agents (like Claude, but all agents do this) have a tendency to leave comments that are over-specific or refer to previous conversational turns that are not relevant to (or even harmful in) the final code.

This type of comment probably helps the agents reason, but should be removed or reworded before shipping.

The same patterns appear in agent-written READMEs and docs. These rules apply there too.

## Rules

1. Flag comments that are unhelpful in these specific ways:
    - **That refer to conversational turns** not relevant to the final PR.
    - **That refer generically to a bug or a fix**.
    - **That refer to standard, idiomatic programming**, especially if it seems like this was added as a "correction" of some sort.
    - **That document folder structure or file layout** (e.g. a header listing sibling files/directories and what each contains). The tree and imports already show this, and such comments go stale the moment a file is added, renamed, or moved.
    - **That enumerate what the code *doesn't* do** (e.g. stacked negations like "never X, no Y, and no Z", for things a reader would not plausibly assume).
    - **That embed regenerable specifics** (litmus test: *would this sentence survive the next routine update?* If no: flag it).
    - **That reassure rather than inform** (e.g. adjectives like "trusted", "reviewed", or "production-ready" which address a reviewer, not a reader).
    - **That use spec-speak** (concepts invented in the PR), especially if they force readers to look up those concepts rather than orienting them.

2. Recommend useful comments:
    - Recommend **removing the comment altogether** if it is obvious from surrounding code.
    - Recommend **a much-shorter comment** (1-sentence, 1 line if possible) for most things.
    - Certainly **remove any language that would not be understandable** without the PR diff or conversation history.
    - Recommend **specific bug numbers & links** if, for the code to make sense, it *must* have a comment explaining the bug.

## Examples

### Documenting previous conversational turns

Incorrect:
```ts
// This is the sole guard against untrusted input — the raw input
// detector was removed — so it gets an explicit regression test.
```

Correct:
```ts
```
(no comment: the raw input detector was removed when iterating on this PR, so the comment refers to something that will not make sense in the squashed history).

### Documents a generic bug

Incorrect:
```go
// Zero out the memory to fix bug #123 where the audio system stopped responding after 10 minutes.
```

Correct:
```go
// If we do not zero-out memory here, AudioSystem::ProcessAudio will think that we still have an
// external processor, so it will slowly stop responding to pings after about 10min. See #123.
```
(documents "why" the code runs, not a generic bug that might not exist in the tracker anymore).

### Documenting folder structure

Incorrect:
```ts
// Variant selector.
//
// Three fully-separated variants live under this folder:
//   - alpha/ : byte-identical to what the v1 checkpoint was trained on.
//   - beta/  : the compact prose used for the beta eval.
//   - gamma/ : self-contained template with its own date rendering.
import { buildAlphaBody } from './alpha/prompt.ts';
```

Correct:
```ts
// Selects the active prompt variant from the PROMPT_VARIANT env var.
import { buildAlphaBody } from './alpha/prompt.ts';
```
(the directory listing duplicates what the file tree and imports already show, and goes stale as soon as a variant is added or renamed; per-variant detail belongs in each variant's own file).

### Enumerating what the code doesn't do

Incorrect:
```md
The resolver performs exactly one outgoing hop. It never traverses the
relationship in reverse and never computes a transitive closure.
```

Correct:
```md
Nickname edges expand one hop out from the given forms — deliberately not chained.
```
(one "deliberately" signals the design choice; the stacked "never"s rebut alternatives a reader never assumed).

### Regenerable specifics in prose

Incorrect:
```md
The current v2 build contains 507 spoken-equivalence groups (1,167 spellings)
and 1,640 nickname inputs (3,354 directed edges). The focused tests cover
workspace validation, multiword given names, surname rejection, and full-name
exactness.
```

Correct:
```md
Counts and provenance are recorded in each JSON artifact; see the resolver
tests for the covered cases.
```
(the counts are wrong after the first data update, and the coverage list goes stale with the next test — the artifacts are the source of truth).

### Explaining idiomatic code behavior

Incorrect:
```cpp
// Read a channel timeline file. A missing file is only benign when the channel
// never wrote any samples; if we recorded samples but the file is gone, that's
// a real I/O fault — let it propagate rather than silently mixing in silence.
```

Better:
```cpp
// Read a channel timeline. Throws on missing file.
```
