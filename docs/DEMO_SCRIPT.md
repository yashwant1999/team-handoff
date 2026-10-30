# Demo script (5 minutes)

Record in a **neutral repository** (this repo, or a dummy project) with neutral handles
(alex, sam). Show no customer or company code. Use two terminals side by side, or two
machines, each at least 110 columns wide so the Team panel shows.

**Before recording**
- The relay is running (`./setup.sh --host alex`); sam has joined with an invite.
- Both run the latest version; both have `/team-panel` open.
- Have a small uncommitted change in sam's repository, so "what changed?" has an answer.

---

### 0:00–0:35 · The problem
> "My team codes with Claude Code all day, but every session is an island. My Claude knows
> what I'm doing; my teammate's Claude knows what *they're* doing. To share any of it we
> stop, open chat, write it up, and wait. team-handoff connects those sessions, and you
> just talk."

Show both terminals with the panel open: TEAM shows each other online, with repo and
branch.

### 0:35–1:20 · Plain-English chat
- Alex types: **"who's online?"**, and Claude answers with the roster.
- Alex types: **"@sam can you check the login flow on your branch?"** The message appears
  in sam's panel (💬), and the status bar counts it if the panel is closed.
- Sam replies from the panel's input box. It shows on alex's side.

> "No commands to learn. Claude maps whatever I say to the right action."

### 1:20–2:30 · Ask a teammate's Claude (the core feature)
- Alex: **"ask sam's Claude what changed on their branch and whether the tests pass"**.
- Alex's panel: `❓ waiting for sam to allow`.
- Sam's panel: the request under **Waiting for you** with **Allow (read-only) / Decline /
  Later**. Sam clicks **Allow**.
- Alex's panel: `⏳ sam answering…`. Sam's Claude runs `git status` and `git diff --stat`
  and reads files, all read-only.
- Sam approves **Send**, and the answer lands on alex's side (🤖). Expand it with ▸.

> "Sam's Claude answered from sam's real context: no context switch for sam, beyond one
> click to allow it and one to approve the answer."

### 2:30–3:15 · Safety
- Say it while showing it: Allow per question, read-only enforced in code (try to show
  the refusal if time allows), Send approval, invite-only access, personal tokens so
  nobody can pose as someone else.
- Briefly show an invite: alex says **"invite sam"** and gets a `tmh1-…` code (one use,
  10 minutes).

### 3:15–3:50 · Handoff
- Alex: **"hand this session over to sam"**. Show the structured summary preview, then
  **Send**.
- Sam's panel: **📦 hands off …** with **▸ read**, then **Accept**. Sam's Claude orients
  itself from the handoff.

### 3:50–4:40 · How it was built with AI
Cut to the repository and docs:
- `docs/AI_DEVELOPMENT.md`: workflow, context engineering (typed API, the repo's
  `CLAUDE.md`, the plugin's own team context), guardrails.
- **"Learning from AI failures"**: pick two, e.g. the `localhost` default found by a
  teammate and fixed with a regression test that fails on the old code, and the
  questions cut off at 200 characters.
- Run `claude plugin test .` and `python3 relay/test_server.py`: 14 tests passing,
  including security and abuse cases.

### 4:40–5:00 · Close
> "One plugin, one tiny relay, no dependencies. Your team's Claudes now work as a team.
> Next: answering in a background helper, a hosted relay with HTTPS, and a conflict
> radar."
