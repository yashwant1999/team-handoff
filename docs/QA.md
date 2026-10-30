# QA approach

AI wrote most of the tests. The human validated them by running the product live with
teammates, and each live failure became a new test. Everything below runs locally in
seconds.

## Run the checks

```bash
claude plugin validate .         # manifest + hooks module, the way Claude Code loads them
claude plugin test .             # 10 plugin tests (tests/panel.test.tsx)
python3 relay/test_server.py     # 4 relay tests against a real relay process
bash -n setup.sh                 # shell syntax
```

A strict TypeScript check runs against Claude Code's shipped API declarations
(`strict`, `noUncheckedIndexedAccess`).

## What the tests cover

### Plugin (`tests/panel.test.tsx`)
The test kit runs the real plugin inside Claude Code's engine. The test stands in for the
engine and the relay, so every network call and UI element is observable.

| Test | Kind | Proves |
| --- | --- | --- |
| the panel shows who is online and the chat | positive | roster rows (name, repo · branch) and chat rows render from relay data |
| /team-panel opens the panel, then closes it | positive | the toggle works both ways |
| a question waits as a card until Allow is pressed | positive + negative | nothing is acknowledged or run before the human decides; Allow sends "typing" and starts the read-only answer |
| Later keeps a request waiting; a decision is kept as a record | edge | Later moves the request into a visible "Later" group and acknowledges nothing; Decline replies and leaves `✗ declined` in the feed; the buttons disappear |
| an invite code joins as the invited handle | positive | the invite decodes, redeems at the right relay, and saves handle, address and personal token |
| after a restart, the relay address saved by an invite is used | **regression** | fails on the old `localhost` default, passes on the fix |
| a long question travels whole; the title is only a preview | edge | a 300+ character question arrives intact; the title stays ≤ 140 characters |
| a message to someone offline says so | edge | the sender is told when the recipient is offline |
| while answering, Claude may read and run read-only git, nothing else | **security / negative** | `git status` and `git log` pass; `git status; rm -rf .`, `git push` and Write are refused |
| the feed keeps all history for scrolling, not only what fits | edge | with 30 messages in a 12-row panel, the oldest and newest are both drawn, so the panel can scroll back |

### Relay (`relay/test_server.py`)
These start the real server on a free port and talk to it over HTTP.

| Test | Kind | Proves |
| --- | --- | --- |
| an invite code becomes a personal token once | positive + negative | redeeming works (case and dashes ignored); a second use is refused |
| a personal token cannot act as someone else | **security** | presence, sending and reading the inbox as another handle return 403 |
| only the host invites and removes | **security** | a member's token can't invite; removing a person revokes their token at once |
| wrong codes are limited | **abuse** | after 10 wrong codes, even a valid code is refused (429) |

## Beyond automated tests

- **Render previews.** For UI changes, a throwaway test mounts the panel with realistic
  data at 64 and 44 columns and prints the layout. This caught rows wrapping mid-word,
  previews showing markdown headings, and duplicated requests before release.
- **Live testing** with two teammates on separate machines over Wi-Fi. This found the
  issues no mock would: firewall rules, a second relay started by mistake, the
  `localhost` default, cut-off questions, and pop-ups interrupting work.
- **Debugging with AI:** `bash -x` traces, the relay's log (it records refused tokens and
  joins with the caller's address), the engine's skipped-hook notices, and step-by-step
  network checks (`curl` with and without a token) to tell "unreachable" from "wrong
  token".
- **A confidentiality sweep** before every push.

## How AI output was validated

- No change shipped on "looks right": validator, types and tests had to pass first.
- For bugs, the regression test was shown to **fail without the fix** before release.
- When a test failed, the first question was whether the *product* or the *test* was
  wrong. One AI-written test was too strict and was corrected (see AI_DEVELOPMENT.md,
  failure #13).
- Final acceptance was always live use by people.
