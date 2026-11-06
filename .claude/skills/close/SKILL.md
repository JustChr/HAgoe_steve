---
name: close
description: Wrap up a HAgoe_steve session cleanly — stop what's running, restore the live system, persist what was learned (repo docs + memory), and leave a short handoff so the next session starts fast. User-invoked only (/close).
disable-model-invocation: true
---

# /close — end the session cleanly, start the next one fast

Two goals: **nothing is left dangling** (processes, live-system changes, unsaved knowledge),
and **the next session can start working within one or two tool calls**, without
re-deriving what this one established.

Be fast: gather state in one batch of parallel calls, don't re-read files already in
context, don't narrate. **Skip any step that has nothing to do** — no background tasks,
no live-system changes, nothing learned, no doc impact → skip it silently. Only step 4
(handoff) and step 5 (report) always run.

## 1. Take inventory

In parallel:
- **Conversation:** what was asked, done, decided, ruled out, and what is still open.
- **Git:** `git status --short --branch`, commits made this session, stashes.
- **GitHub:** `gh pr list` and the latest release (`gh release list -L 1`) — anything opened,
  merged, closed or released this session.
- **Running things:** background shells and monitors started this session (MQTT sniffers,
  watchers).
- **Live-system changes:** anything switched or set on the live Home Assistant instance or
  the go-e for testing — typically the *Smart control* switch, the *force state* select,
  the charging mode, `frc`/`amp`/`psm` written directly. Note the pre-session value from
  the conversation.

## 2. Close loops

- **Stop** every background task / monitor started this session.
- **Restore** each live-system change to its pre-session value and **read it back** to
  verify (HA REST: `GET /api/states/<entity>` with `Authorization: Bearer $HA_TOKEN`).
  If the original value is unknown or access fails, say so in the report — never silently.
- **Reusable scripts:** the scratchpad dies with the session. A script worth having again
  (sniffer, sim, query) goes to `tools/`, or its recipe into a `reference` memory.
- **Uncommitted code changes** (not docs): list them and ask once — commit / leave / discard.
  Don't delete branches or remote state unless the user asked.

## 3. Persist knowledge — each thing in exactly one place

| Kind | Goes to |
|---|---|
| Changed engine behaviour | `docs/charging-behavior-matrix.md` |
| Verified go-e / MQTT facts (enums, firmware behaviour, live test results) | `docs/mqtt-direct-concept.md` |
| Phase history, open follow-ups, investigated-but-not-built | `BACKLOG.md` |
| User-visible behaviour change | `README.md` + `info.md` (same story) |
| A new repo gotcha future work must know | `CLAUDE.md` |
| How the user wants me to work | `feedback` memory (**Why** + **How to apply**) |
| The user, external systems, access (where, not the secret) | `user` / `reference` memory |

**Repo doc updates are pre-approved:** commit them (`Docs: <summary>` + the Co-Authored-By
trailer) and push to `main` without asking. Code changes are not covered by this — see step 2.

Memory hygiene (only for memories this session touched or proved wrong):
- Update instead of adding near-duplicates; correct or delete what turned out stale
  (a login that stopped working, a superseded plan).
- Absolute dates. No secret values — record where they live (e.g. env var `HA_TOKEN`).
- Don't store what the repo or git history already says.
- Keep `MEMORY.md` at one line per memory and in sync with the files.
- **Status lives only in the handoff.** If another memory carries its own "Status (date): …",
  replace it with a pointer to [[session-handoff]].

## 4. Write the handoff (always)

Overwrite `session-handoff.md` in the memory directory — the next session's starting
point, not a log. Under ~25 lines:

```markdown
---
name: session-handoff
description: Where the last session stopped (YYYY-MM-DD) — read first, verify before trusting
metadata:
  type: project
---

**Last session:** YYYY-MM-DD — <one-line theme>

**State:** branch, last commit / release, clean or not, live system restored or not.

**Done:** 2–5 outcomes (not activity).

**Open / next:** concrete next step(s) in priority order, each actionable as written —
or "nothing open".

**Watch out:** blockers, things waiting on the user, traps found this session.

**Pointers:** files, PRs, docs, memories ([[name]]) the next step needs.

**Verify:** `git log --oneline -1 && gh pr list && gh release list -L 1`
```

Write what git can't tell: intent, decisions and their reasons, what was ruled out and why.
If the file changed since this session started (another session closed in between), merge
its open items instead of dropping them.

`MEMORY.md` gets this line **at the top** (only the index is auto-loaded, so the line must
stand on its own):
`- [Session handoff](session-handoff.md) — YYYY-MM-DD: <theme>; next: <step>. Read first.`

## 5. Report (always)

A short message:
- closed / restored — and anything that could **not** be,
- what was saved where (commit hash for docs, memory files),
- the next step from the handoff,
- the pending question from step 2, if any.

No recap of the session beyond that.
