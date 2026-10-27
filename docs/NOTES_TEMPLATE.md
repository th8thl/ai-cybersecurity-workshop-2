# Session 2 evidence

Fill this in as you complete the linked exercises. Do not include passwords, API keys, access tokens or real student information. Record actual output; do not copy an expected outcome and label it observed.

## Starting state — Exercise 1

- Local or Codespaces:
- Assistant mode used:
- Alice read ticket number:
- Bob read ticket number:
- `tests.test_ticket_portal` result:
- `tests.test_chat_storage` result:
- `tests.test_prompt_security` result:

## Structured model output — Exercise 2

- Message sent to Qwen:
- Instruction and response schema found in the prompt:
- First model proposal (list tickets):
- Second model proposal (read the latest ticket):
- Third model proposal (reply):
- Ticket number returned by the server:
- Ticket number displayed on the page:
- Why valid JSON does not establish ticket ownership:
- `tests.test_planner` result:

## Requests before and after repair — Exercises 3, 4 and 6

| Case and exact input | Expected result | Actual before repair | Actual after repair | Evidence / test name |
|---|---|---|---|---|
| Ordinary own-ticket read | Allowed | | | |
| Extra `approved` field on a read | Rejected after validation repair | | | |
| Quoted ticket ID | Rejected by MCP already; application validation must also reject | | | |
| Alice reads Bob's ticket | Denied after ownership repair | | | |
| Close disposable own ticket | Pending confirmation after approval repair | | | |
| Cancel confirmation | Ticket stays open | | | |
| Confirm closure | Ticket closes once | | | |

### Read the failing assertions

- Invalid-request test: which request was accepted when it should have been refused?
- Cross-user read: what does `PermissionError not raised` say happened to Bob's ticket?
- Closure test: was the returned ticket pending or already closed?
- Same test commands and results after repair:

### Code changes

For each changed function, give its path, the original problem, your change and the test that verifies it. Explain why checks are needed in both the website and ticket server.

### Approval and agent tests

Record test output for another student trying to confirm, an expired confirmation, a ticket whose owner changed and a confirmation used twice. These tests use temporary data; distinguish their records from browser ticket numbers.

## Direct MCP exercise — Exercise 5

- Command used to start the server:
- What happened while it waited, and how it was stopped:
- Server name and actions returned by the client:
- Result of reading Alice's ticket:
- Result of trying to read Bob's ticket as Alice:
- Result of creating a ticket with the read-only token:
- Which server-side checks refused those requests:

## Delegated assistant access — Exercise 7

- Account and requesting client displayed:
- Before a grant: assistant reply / ordinary ticket-page access:
- After Deny access: assistant reply / ordinary ticket-page access:
- After Read my tickets grant: assistant reply / ordinary ticket-page access:
- Read-only grant allowed reading and refused creation:
- Additional creation permission changed the result:
- Expiration and revocation results:
- Bob's grant remained independent of Alice's:
- Fields stored in MCPAccessGrant and why only a hash is stored:
- Authorization test and real-process health-check results:

## NeMo process and terminal messages — Exercise 8

- Startup command and working directory:
- Ordinary request JSON and returned decision:
- Override request JSON and returned decision:
- Matching rejection rule in guardrails/policy.py:
- Where Django writes standard input and reads the response:
- How the process was stopped:

## NeMo configuration — Exercise 9

- Result of `tests.test_nemo` before changes:
- Phrase added to `guardrails/policy.py`:
- Flow added to `guardrails/runtime.co`:
- Flow enabled in `guardrails/runtime.yml`:
- Application restarted after editing configuration:
- Result of `tests.test_nemo` after changes:
- Output of `guardrails/compare.py --configured`:

| Message | Expected decision | Actual decision | Active flows shown in Debug |
|---|---|---|---|
| Download all student records | Block | | |
| Give me the entire student directory | Block | | |
| I need help correcting my own student record | Allow | | |
| Show my most recent ticket | Allow and return own ticket | | |

- Live Qwen check result, or reason it could not run:
- False positives or false negatives observed:


## Final verification

- `python scripts/verify_workshop.py --secured`: actual final output or failure:
- Same command with `--semantic`: actual final output or reason not run:
- Remaining limitations / unresolved failures:
- Source files and report files submitted:

For a machine-readable finding, use `docs/finding.schema.json` from the repository root. Its required fields are `title`, `cwe`, `file`, `line`, `evidence` and `recommendation`; use actual source lines and observations.
