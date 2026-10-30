# team-handoff: command cheat sheet

## 0. Or just ask Claude

After installing, every step below can be said in plain English:
"host the team relay here, I'm alex", "join the team relay as sam, url …, token …",
"is my team setup working?", "stop the team relay".

## 1. Host the relay (one person, once)

Only the host does this. Everyone else skips to section 2. A second relay makes a
separate team that nobody else is on.

```bash
cd ~/Projects/team-handoff
./setup.sh --host <your-handle>     # start or restart the relay; prints the /team-join line
./setup.sh --stop                   # stop it
PORT=8788 ./setup.sh --host <you>   # if port 8787 is busy
```

| What | Where |
| --- | --- |
| Team token (reused on restart) | `~/.local/share/team-handoff/token` |
| Relay log | `~/.local/share/team-handoff/relay.log` |
| Relay process id | `~/.local/share/team-handoff/relay.pid` |
| Your config | `~/.config/team-handoff.json` |

Check the relay is up: `curl -H "X-Team-Token: $(cat ~/.local/share/team-handoff/token)" http://localhost:8787/members`

## 2. Teammates join (two lines in Claude Code)

```
/plugin install team-handoff --marketplace yashwant1999/team-handoff
/team-join <their-handle> http://<relay-host>:8787 <token>
```

Share the `/team-join` line privately, because it holds the token.

## 3. Just say it (plain English)

| You type | What happens |
| --- | --- |
| who's online? | lists the team, marking you and your link |
| connect me with dev2 | dev2 accepts; the status bar shows `🔗 dev2 ●` |
| tell dev2 the field doesn't exist yet, with what I found | Claude writes up your findings and sends them |
| @dev2 is the PR merged? | message to dev2 |
| @team build is green again | message to everyone online |
| ask dev2's Claude how the router is generated | dev2 allows; `⏳ dev2 answering…`; the answer lands here |
| ask the team who knows how the release build is signed | every online Claude answers; Claude merges them |
| what did dev2 say? | recent team messages |
| hand this over to dev3 | summary, you preview, dev3 accepts |
| set my status to fixing the login bug | the team sees it in `/team` |
| disconnect | ends the link on both sides |
| open / close the team panel | toggles the side panel |

## 4. Slash shortcuts

| Command | What it does |
| --- | --- |
| `/team-panel` | open or close the Team side panel (chat, request cards, who's online) |
| `/team` | who's online, you, your link, their branches |
| `/team-join <handle> <url> <token>` | save your config and connect |
| `/connect <user>` · `/disconnect` | link with one teammate |
| `/say [@user\|@team] <text>` | message the linked teammate, someone else, or everyone |
| `/ask [@user\|@team] <question>` | ask a teammate's Claude, or the whole team |
| `/handoff [@user] [note]` | hand this session over |
| `/handoff-request @user [why]` | ask a teammate for their session's context |
| `/team-status <text>` | set your status |
| `/team-inbox` | recent messages, and anything you put off with **Later** |

## 5. Test alone on one machine

Terminal 1 is you, with the plugin installed. Terminal 2 plays a teammate:

```bash
TEAM_HANDOFF_USER=dev2 claude
```

Then in terminal 1: `connect me with dev2` → **Accept** in terminal 2 → try the
phrases above.

## 6. Update and troubleshoot

```
/plugin update team-handoff       # get the latest version
/reload-plugins
```

| Symptom | Fix |
| --- | --- |
| "not set up" | run `/team-join …` |
| status shows `relay unreachable` | relay down (`./setup.sh --host <you>`), wrong URL, or firewall on port 8787 |
| "refused the team token" | the token changed; get the new `/team-join` line |
| relay won't start | `tail ~/.local/share/team-handoff/relay.log`; port busy → `PORT=8788` |
| two terminals show the same handle | set `TEAM_HANDOFF_USER` in the second one |
| a teammate started their own relay by mistake | they say "stop the team relay", then re-run the host's `/team-join` line |
| see who tried to connect, from the host's side | `tail -f ~/.local/share/team-handoff/relay.log` (shows refused tokens and new members with their IP) |
