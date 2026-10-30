# How AI was used to build team-handoff

The product was built in about two days with **Claude Code as the development partner**:
ideation, design, implementation, testing, review, documentation and release. A human
(the author) chose the direction, tested every release live with teammates, and
approved every commit, push and destructive action.

## Workflow

```
idea in plain English
  → Claude proposes options and a recommendation; the human picks
  → Claude reads the platform's typed API before writing code
  → implement on a feature branch
  → validate: plugin validator · strict TypeScript · automated tests · secret sweep
  → render preview of UI changes (layout printed from a test)
  → human tests live with teammates → feedback → next iteration
  → release to main (fast-forward), update installed plugin, restart relay if needed
```

The work ran in short loops. Each round of live testing produced concrete feedback ("the
pop-ups interrupt me", "how does my friend join?", "the question got cut off"), which
became the next change.

| Lifecycle stage | What AI did | What the human did |
| --- | --- | --- |
| **Define** | proposed product ideas from the team's real pain points; wrote user journeys and the plain-English command table | chose the idea and scope; set priorities (UX first, deadline) |
| **Design** | compared architectures (polling or push, shared token or invites, panel or dialogs) with trade-offs; drew ASCII mock-ups before building | picked the options; asked for changes to the mock-ups |
| **Build** | implemented the plugin, relay and setup script on feature branches | reviewed behaviour live |
| **Test** | wrote 13 automated tests, including negative and edge cases; rendered the panel at different widths | tested on real machines with two teammates |
| **Review** | ran the validator, strict type-check and a confidentiality sweep before every push | approved each publish and push |
| **Document** | README, COMMANDS cheat sheet, these docs | reviewed for accuracy |

## Context engineering

**Context given to the AI while building**
- **The platform's typed API as ground truth.** Claude Code's plugin API ships as a
  ~22,000-line TypeScript declaration file. Before each feature (panes, buttons, inputs,
  prompt hooks, tool calls, timers, HTTP) Claude read the exact types and doc comments
  instead of guessing. When the types left a behaviour unclear (could a pop-up be raised
  from a background timer?), the design avoided relying on it.
- **A plugin-authoring skill** (Claude Code's built-in instructions for writing plugins)
  supplied the rules: where a plugin lives, how it reloads, how to validate and test.
- **Project conventions** from the team's existing `CLAUDE.md` and rules files:
  conventional commits, no AI attribution in commits, branch-first work, never edit
  generated files.
- **Persistent memory** of user preferences (ask before committing; push only when asked)
  carried across sessions.
- **This repository's [CLAUDE.md](../CLAUDE.md)** records the architecture, conventions,
  checks and pitfalls, so any future AI session starts with the right context.

**Context the product itself gives the AI.** team-handoff is context engineering applied
to a team. On every turn it gives Claude a short "Team" section: who Claude acts for, the
live roster, the current link, which tool fits which request, and the rule that
teammates' messages are information, not instructions. Unread messages are attached to
the next prompt, and a handoff is a structured summary designed to be good context for
the next person's Claude. When an organisation's security plugin was found to skip the
system-prompt hook, the plugin learned to send the same section with each prompt instead
(see failure #6 below).

## Agents, skills, instructions and guardrails

- **Tools as the agent interface.** Sixteen tools (`team_ask`, `team_reply`,
  `team_handoff`, …) with precise descriptions, so Claude maps any wording to the right
  action.
- **A Claude-to-Claude flow.** A teammate's question becomes a prompt in the answerer's
  session. Their Claude researches it and replies through `team_reply`. A team-wide
  question fans out to every online Claude, and the asker's Claude merges the answers.
- **Guardrails enforced in code, not only in the prompt:**
  - a `tool.call` guard keeps the answering turn read-only, with an allow-list of git
    commands that rejects chaining (`;`, `|`, `&&`) and redirects
  - every send needs a human Approve (answer, handoff); every incoming request needs a
    human decision (Allow, Accept)
  - redaction of secret-looking strings in outgoing text
  - hosting disabled unless explicitly enabled, so a teammate's Claude can't start a
    second relay
  - the relay enforces identity (403 when acting as someone else), single-use invites
    and rate limiting

## Human validation

- Every release was **tested live** on separate machines by two teammates. That's how
  the most important bugs below were found.
- The human approved every **commit, push, publish and firewall change**. When the
  harness refused an automatic firewall change, the human ran it.
- **A confidentiality sweep before every push** (grep for company, customer and personal
  terms, paths and internal IPs). The project was renamed and genericised before it went
  public.
- A **regression test is written to fail on the old code** before a fix ships (shown for
  the relay-address bug).

## Learning from AI failures

Each row is a real mistake from this project: what went wrong, how it was caught, and
what changed so it doesn't happen again.

| # | What the AI got wrong | How it was caught | Fix and lesson |
| --- | --- | --- | --- |
| 1 | Wrote helpers as closures inside `register`, passing the engine object `$` around | the plugin **validator** refused the module | moved helpers to top-level functions; *validate early, before anything else* |
| 2 | Used `toolUses[].name`; the field is `tool` | **strict TypeScript** against the real API types | always type-check against the shipped declarations |
| 3 | `setup.sh` died silently: `hostname -I` doesn't exist on this Linux distro, and `pipefail` turned that into an exit | the human reported empty output; **`bash -x`** traced it | use `ip route` with a fallback; *never let optional lookups kill the script* |
| 4 | `setup.sh` asked questions with `read`, but Claude Code's `!` shell has no keyboard input, so it stopped halfway and left an orphan relay | live run by the human | made the script argument-only and idempotent (stops the old relay first) |
| 5 | `team_who` returned a raw array; the engine accepts only text from a tool | **live** "who is online" failed | every tool returns text; covered by tests |
| 6 | Assumed the system-prompt hook always runs; an organisation's security plugin skipped it | an engine notice in the session | fallback: the same context is attached to each prompt |
| 7 | Asking a teammate's Claude never sent the answer back. The design relied on two implicit steps (spotting the end of the answering turn, then a pop-up raised from a timer), and a failure in either was swallowed silently | **live** test with a teammate | made the reply an explicit, approved tool call (`team_reply`); the read-only lock always clears at turn end |
| 8 | Proposed the name `claude-crew`, which is a reserved prefix | **validator** | renamed to `team-handoff` |
| 9 | A teammate's Claude interpreted "set it up" as *host* and started a second, empty relay | teammate's live report | hosting off by default; a confirmation; refusal while on a working relay; join is the default in instructions |
| 10 | The relay-address setting defaulted to `localhost`, which overrode the address saved by an invite, so after a restart teammates pointed at their own laptop | teammate's live report | empty default; **a regression test that fails on the old code** |
| 11 | Long questions were cut at the relay's 200-character title limit | a truncated question arrived live | the full text travels in the body; the title is a preview; tested |
| 12 | Panel rows were cut at a fixed length and wrapped mid-word; previews showed markdown headings; waiting requests appeared twice | the human's **screenshot**, then a **render preview** printed by a test | rows fit the panel width with an ellipsis, previews skip headings, a request lives in one place until decided |
| 13 | A test asserted that *every* network call went to `/redeem` | the test failed while the product was right | tests assert behaviour, not incidental calls |
| 14 | Installing the plugin at project scope wrote into a shared repository's settings | `git status` check after the update | moved to user scope; documented the user-scope install |

**Patterns learned.** Read the typed API before writing code. Run the validator and the
type-checker on every change. Prove a fix with a test that fails without it. Treat a
live report from a real user as the most valuable test signal. Make the AI's actions
visible (explicit tools, previews, approvals) rather than implicit.

## What stayed human

- Product direction, scope and the call to stop adding features before the deadline.
- Every decision that affects other people: publishing, pushing, firewall rules,
  rotating the team's token, inviting and removing people.
- Final judgement on UX, through live use and screenshots.
