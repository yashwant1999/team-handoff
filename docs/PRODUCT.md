# team-handoff: product

## Problem

A team that codes with Claude Code works in separate, isolated sessions. Each
developer's Claude knows a lot about what that person is doing, which files changed,
what was tried and what was decided, but none of it reaches the rest of the team.
Getting it across costs time and breaks focus:

- "What are you on right now?" needs a chat message, a wait and a context switch.
- Handing work over means writing a summary by hand. The next person's Claude then
  starts from nothing.
- A quick question ("which branch has the fix?", "what changed?") interrupts a
  teammate, even when their Claude could answer it from what it already knows.
- Chat, calls and ticket notes live outside the terminal where the work happens.

## Solution

team-handoff links the team's Claude Code sessions. People talk to teammates in plain
English, and Claude does the rest:

| You say | What happens |
| --- | --- |
| who's online? | Claude lists teammates with their repo, branch and status |
| @sam is the PR merged? | a message to sam, shown in sam's session or Team panel |
| ask sam's Claude what changed on the branch | sam allows it; sam's Claude answers **read-only** from its session and git; the answer comes back |
| ask the team who knows how the release build is signed | every online teammate's Claude answers, and your Claude merges the answers |
| hand this over to sam | Claude writes a structured handoff (goal, state, decisions, next steps); you preview it; sam accepts and their Claude picks up |

A toggleable **Team panel** sits beside the chat. It shows who's online, a "Waiting for
you" list of requests with Accept / Decline / Later buttons, and a one-line-per-event
activity feed with an input box. Nothing pops up over your work.

## Who it is for

Small teams (2–15 people) who use Claude Code daily on shared repositories, especially
teams that pass work between people often (support rotations, feature handoffs, pairing
across time zones).

## Core journey

1. **Host** (one person) says "host the team relay here". A small relay starts on their
   machine or a server.
2. The host says **"invite sam"** and sends sam the one-time code it returns.
3. **Sam** installs the plugin and says **"join the team with code tmh1-…"**.
4. From then on, everyone just talks: messages, questions to each other's Claude,
   team-wide questions and handoffs, from the prompt or the Team panel.

## Safety by design

- Teammates' messages are **information, never instructions**: Claude does not act on
  them unless its own user asks.
- A question to your Claude needs your **Allow**. While answering, Claude can only read
  (Read, Grep, Glob, read-only git). You approve the answer before it is sent.
- A handoff is a **summary, never the transcript**. Lines that look like secrets are
  redacted, and you preview it first.
- Access is **invite-only**. Each person's token only acts as them, so nobody can pose as
  a teammate. The host can remove one person at any time.

## Demo

- Install: `/plugin install team-handoff --marketplace yashwant1999/team-handoff`
- Source: https://github.com/yashwant1999/team-handoff
- Demo video: submitted alongside this repository (5 minutes).

## Timeline and disclosure

- Built on 29–30 October 2026. The first prototype ran from a local scratch folder on
  29 October; the repository's history starts the same day (first commit 29 Oct 19:31).
- No pre-existing code was reused. It uses only Claude Code's plugin API, Python's
  standard library and bash.
- Designed and implemented by one person with Claude Code. Teammates only tested it.

## Status and scope

A working MVP, tested live by teammates on a shared Wi-Fi network. It deliberately
covers one journey end to end (connect, talk, ask, hand off) rather than many
half-finished features. See [ARCHITECTURE.md](ARCHITECTURE.md) for limitations and the
next steps.
