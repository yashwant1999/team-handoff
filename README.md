# team-handoff

Links the team's Claude Code sessions. Talk to teammates in plain English. Claude
messages them, asks their Claude to research something, asks the whole team at once,
or hands your session over. Every incoming question waits for the receiver's
**Allow**, and their Claude answers read-only.

## Install (teammates)

```
/plugin install team-handoff --marketplace yashwant1999/team-handoff
/team-join <your-handle> <relay-url> <token>
```

The person hosting the relay gives you the `/team-join` line.

## Host the relay (one person, once)

```bash
./setup.sh --host <your-handle>      # starts relay/server.py, prints the /team-join line
./setup.sh --stop                    # stops it
```

Run it on a machine the whole team can reach, such as an office server, a small VM or a
Tailscale node. Use HTTPS beyond the office network.

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
`/ask [@user|@team]`, `/handoff`, `/team-status`, `/team-inbox`, `/team-join`.

## Safety

- A teammate's message is information. Claude never acts on it unless you ask.
- A question to your Claude needs your **Allow**. While answering, Claude can only
  Read, Grep and Glob. You approve the answer before it is sent.
- A handoff is a summary, never the transcript. Lines that look like keys or tokens
  are redacted, and you preview the summary before it is sent.
