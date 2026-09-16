---
# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later
name: commit-message
description: Write Conventional Commits messages for the current changes, splitting them into several commits when they cover several concerns, and propose each message for review before anything is committed. Use whenever the user asks for a commit message, asks to commit the current changes, or invokes /commit-message.
---

# Commit message

Draft the message, then let the user have the last word: the commit is theirs to
approve. Staging is yours to arrange, so is proposing more than one commit — but
nothing is committed before they have read the message and said to go ahead.

## Workflow

### 1. Survey the changes

```bash
git status --short
```

Then read the actual diffs, `git diff --cached` and `git diff`. Untracked files
count too: they are part of the change even though no diff shows them.

Whatever is **already staged is a signal**: the user chose that scope. Write for
it, and ask before widening it. When nothing is staged, the grouping is yours to
decide.

### 2. Decide the split

One commit per concern. A fix and the refactor that made room for it are two
commits; a change and its tests are one.

For a single commit, go on. For several, **propose the plan before touching the
index** — a numbered list, each entry a subject line plus the files it takes —
and let the user confirm or rearrange. Then run the rest of this workflow once
per commit, in the listed order, stopping if one is aborted.

Staging is file-level: `git add -- <paths>`. The interactive flags (`git add -p`,
`-i`) are unavailable here, so when one file has to be split across two commits,
say so and let the user split it themselves.

Before each commit of a plan, make the index hold exactly the files of that
commit — the commit command carries no pathspec and takes the index whole:

```bash
git add -- <paths of this commit>
git reset -q -- <paths of the later commits>
```

`git reset` on paths leaves the working tree untouched, and unlike
`git restore --staged` it also works before the very first commit of a
repository. A file that `git status --short` marks in both columns (`MM`, `AM`)
is only partly staged, though, and unstaging it drops that split — ask first.

### 3. Gather the why

The diff shows *how*; the message must say *why*. Use the conversation, the
linked issue, `git log` on the touched files, and the branch name. If a reason
is missing, ask rather than guess — and never invent an issue number.

### 4. Draft it

Follow *Format*, *Content* and *Trailer* below. `git log -20` is the reference
for tone, not for format: much of the history predates the rules below.

### 5. Write it to the git dir

A quoted heredoc, so nothing in the message expands:

```bash
cat > "$(git rev-parse --git-path CLAUDE_COMMIT_MSG)" <<'EOF'
<the message>
EOF
```

### 6. Verify the line limits

This prints every offending line; silence is a pass. Rewrite until it is
silent — never truncate mid-sentence.

```bash
awk 'NR==1 ? length>50 : (length>72 && !/^[A-Za-z-]+-by: /) {printf "L%d (%d): %s\n", NR, length, $0}' \
  "$(git rev-parse --git-path CLAUDE_COMMIT_MSG)"
```

### 7. Propose it

Print the message in the reply, whole, in a fenced block, followed by the path
of the draft file. Then stop there: never commit in the turn that proposes.

The user changes it either way — by replying with what to fix, or by editing the
draft file themselves. When they reply with corrections, rewrite the file, check
it again with step 6, and propose the new version the same way.

### 8. Commit

Only once the user has agreed to it. They may have edited the draft or the
index in the meantime, so check both before committing: read the file again and
rerun step 6 over it, and confirm `git status --short` still stages exactly the
files of this commit. A staged scope that has drifted stops the commit — report
what changed and ask. A line the user's own edit made too long stays theirs to
keep, so only flag it. Then commit what the file holds:

```bash
git commit --file "$(git rev-parse --git-path CLAUDE_COMMIT_MSG)"
```

A non-zero exit is a genuine failure, not a signal: report what git printed, and
leave the rest of the plan alone until it is sorted out. Otherwise show
`git log -1 --oneline` and carry on with the next commit.

## Format

`<type>(<scope>): <subject>`

- Subject: 50 characters maximum, imperative mood ("add", not "adds"),
  lowercase start, no final period.
- Body: wrapped at 72 characters, blank line after the subject.
- Bullets: `*`, never `-`, however many `-` the older history holds.
- Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `style`, `perf`,
  `build`, `ci`, `revert`.
- Scope: the module under `rero_ils/modules/` that the change touches
  (`patrons`, `items`, `loans`, `documents`). Outside `rero_ils/modules/`, use
  the area, as the history already does — `scripts`, `docker`, `deps`, `tests`,
  `theme`, `circulation`. Check with
  `git log --format=%s | grep -oP '^\w+\(\K[^)]+' | sort | uniq -c | sort -rn`.
  Omit the scope when the change is repository-wide. An issue number is never a
  scope.
- `!` before the colon marks a breaking change: `feat(patrons)!: ...`.

## Content

Explain *what* and *why*, not *how* — the code says how, so the body is never a
technical list of the changes made. It answers one question, why the change was
necessary, and stops there: a developer should grasp the change and its context
before opening the diff.

Keep it short. Two to six `*` bullets, each carrying a reason rather than a file
name; add an opening paragraph only if the motive does not fit in the bullets.
Cover the motive of the commit, not its incidental fallout — whatever the diff
makes plain on its own earns no bullet.

Too verbose:

> The commit conventions lived in CLAUDE.md, where they were loaded into
> every session whatever the task at hand, and where they could only ever
> be a format spec: they described the shape of a message without saying
> anything about how to arrive at one.
>
> * A skill loads on demand, so the rules reach the context only when a
>   commit is actually being written.
> * As a workflow rather than a list of rules.
> * The draft is proposed for review, so the message is always read
>   before it is committed and the commit stays the author's own.
> * Ignore the local Claude settings, whose permission allowlist is
>   personal to each developer's machine.

Enough, for that very same commit:

> * Create a skill for commit conventions to avoid loading it into
>   every session.
> * Specify the conventions to make commit messages more readable and
>   standardised.

The opening paragraph only restates the first bullet; the review step and the
`.gitignore` entry are plain from the diff and were never the point of the
commit. Each bullet is a concise description of a broad change and the motive for it.

Close with the issue when there is one, as its own bullet: `* Closes #3663.`
Never open a line with `#`, there or anywhere in the body: git takes it for a
comment and drops it without a word.
Flag a manual migration step under a `:warning:` paragraph.

## Trailer

Credit the humans, one per line, in the last paragraph, as
`Co-Authored-by: <name> <email>`. Read the pair from `git config user.name` and
`git config user.email` — never from an example or from memory — and add any
colleague the user names. Do not sign this section as an LLM: no Claude or
Anthropic trailer, whatever the default of the harness is.
