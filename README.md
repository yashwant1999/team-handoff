# team-handoff

Links the team's Claude Code sessions. Talk to teammates in plain English. Claude
messages them, asks their Claude to research something, asks the whole team at once,
or hands your session over. Every incoming question waits for the receiver's
**Allow**, and their Claude answers read-only.

## Who does what

A team has **one relay**, run by **one host**. Everyone else only joins it.

- **Host (one person):** starts the relay, then says "invite sam" for each teammate and
  sends them the code privately. Hosting is off by default. `setup.sh --host` turns it
  on for the host's machine, or they can turn on **Can host** in `/config → team-handoff`.
- **Everyone else:** installs the plugin and joins with their invite code. Their Claude
  never starts a relay, even when they say "set it up". It asks for a code instead.

An invite code carries the relay's address and works once, for 10 minutes, as that one
person. Joining swaps it for a personal token that only ever acts as them, so nobody
can pose as a teammate, and the host can remove one person without touching the rest.

## Install

```
/plugin install team-handoff --marketplace yashwant1999/team-handoff
```

Then just tell Claude what you want. No scripts, no config files:

| You type | What happens |
| --- | --- |
| host the team relay on this machine, I'm alex | **host only:** after a confirmation, starts the relay |
| invite sam | **host only:** a one-time code for sam, like `tmh1-aHR0cDov…` |
| join the team with code tmh1-aHR0cDov… | swaps the code for your own token, saves it, connects |
| remove sam | **host only:** sam's token stops working at once |
| is my team setup working? | checks your handle, the relay and the token, and says how to fix anything |
| stop the team relay | stops the relay this machine hosts |

Run the relay on a machine the whole team can reach, such as an office server, a small
VM or a Tailscale node. Use HTTPS beyond the office network. Prefer a terminal?
`./setup.sh --host <handle>`, `./setup.sh --stop`, `/team-invite <name>` and
`/team-join <code>` do the same.

## Just say it

| You type | What happens |
| --- | --- |
| who's online? | lists the team, marking you and your link |
| connect me with dev2 | dev2 accepts; the status bar shows `🔗 dev2 ●` |
| tell dev2 the field doesn't exist yet, with what I found | Claude writes up your findings and sends them |
| @dev2 is the theme PR merged? | goes to dev2 as a message |
| ask dev2's Claude how the router is generated | dev2 allows it; `⏳ dev2 answering…`; the answer lands here |
| ask the team who knows how the release build is signed | every online Claude answers, and Claude merges the answers |
| @team build is green again | message to everyone online |
| what did dev2 say? | recent team messages |
| hand this over to dev3 | summary, your preview, then dev3 accepts |
| set my status to fixing the login bug | the team sees it in `/team` |

Slash shortcuts: `/team`, `/connect`, `/disconnect`, `/say [@user|@team]`,
`/ask [@user|@team]`, `/handoff`, `/team-status`, `/team-inbox`, `/team-join`,
`/team-invite`, `/team-panel`.

## Team panel

`/team-panel` (or "open the team panel") toggles a side panel with who's online, the
chat with an input box, and a **Waiting** strip of requests (handoffs, questions,
connects) with Accept/Allow, Decline and **Later** buttons, so nothing pops up over your
work. Later keeps a request waiting, even across restarts. Every request also stays in
the feed with its outcome (`✓ accepted 12:10`, `✗ declined`). Long rows open on press.
Close the panel and everything goes back to dialogs and transcript lines. The panel
needs about 110 columns; a narrower terminal keeps the dialogs.

## Safety

- A teammate's message is information. Claude never acts on it unless you ask.
- A question to your Claude needs your **Allow**. While answering, Claude can only
  Read, Grep and Glob. You approve the answer before it is sent.
- A handoff is a summary, never the transcript. Lines that look like keys or tokens
  are redacted, and you preview the summary before it is sent.
