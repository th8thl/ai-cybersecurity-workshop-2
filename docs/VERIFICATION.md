# Implementation verification

The complete documented verification command passed in both application folders
on October 25, 2026. These checks used the existing Python environment; no
packages, account passwords or provider settings were changed.

## Commands and results

Run from the folder containing `manage.py`, with its existing environment active:

```text
python scripts/verify_workshop.py
```

| Folder | Verified result |
|---|---|
| `starter/` | 70 baseline tests passed. The real-process check reproduced the intentional cross-user access and missing-confirmation flaws, while enforcing consent, token permissions, expiry and revocation. Bandit reported 7 review findings and Semgrep reported 3 expected vulnerability findings. |
| `solution/` | All 109 tests passed. Real MCP/NeMo integration and human confirmation checks passed. Semgrep reported no workshop-rule findings. Bandit reported 5 lower-severity review findings and no HIGH findings. All seven configured NeMo comparisons matched their expected decisions. |

Both commands ended with `All requested workshop checks passed.` This does not
claim that every possible security issue has been found. The initial application
still has the weaknesses that students repair in the exercises.

## Authorization and real MCP checks

`tests/test_authorization.py` contains 17 tests for explicit consent, denial,
hash-only token storage, user/client/audience binding, permission selection,
expiration, revocation, replacement, separate users, forged tokens, HttpOnly
cookies, login, CSRF, POST-only revocation and token redaction. Opening a page
never issues a token. An authorized client cannot call a confirmation tool.

`scripts/healthcheck.py` starts actual MCP child processes with temporary users,
database records and deliberately created test grants. It verifies that the
server refuses absent, unknown, expired, revoked and replaced tokens. A direct
server call with a read-only token cannot create a ticket even when it bypasses
the normal client helper. Client discovery exposes only granted tools to the
model. No browser user's grant is created or changed by these checks.

The secure integration check also confirms closure through the authenticated
ticket page with CSRF enforcement, then verifies that confirmation cannot be
reused. MCP has no confirmation tool.

## Browser checks

An isolated local preview used a disposable database and Alice test account.
Ordinary ticket pages worked before consent. Denying consent left the assistant
without access. A read-only grant allowed reading the most recent ticket and
refused creation with a specific missing-permission message. Replacing the grant
with read and create permissions allowed the same creation request. Revocation
blocked the next assistant read while retaining ordinary ticket access.

Chat requests remained asynchronous, Enter submitted, the answering indicator
appeared, and returned ticket links were marked to open in a new tab. Browser
checks used Demo mode with the real MCP and NeMo processes. Live Qwen was not
part of this authorization verification run; the optional `--semantic` check
remains available.

## Database and configuration preservation

The `chatbot.0003_mcpaccessgrant` migration was tested on a copy of the existing
database before application to the local working database. It adds authorization
records. Every pre-existing row was compared and retained, foreign-key integrity
passed, and no real user grant was issued. The `.env` file was unchanged.
Accounts, password hashes, tickets, approvals, attachments, audit records,
conversations and sessions were preserved.

The obsolete generated service vault files and their implementation were removed.
Users now grant access through **Assistant → Authorize assistant**. The database
stores grant metadata and token hashes; the browser receives the client token.
See [the authorization flow](MCP_AUTHORIZATION.md).

## Existing application checks retained

The suite still covers normal ticket pages independent of AI, structured model
planning, schema validation, ownership, closure confirmation, conversation
storage, verified outcomes, NeMo, JSON imports, private attachments and migration
preservation. File tests use temporary uploads. The harmless pickle test prints
only a marker; attachment tests check unauthorized directory and cross-user reads.

Bandit and Semgrep scan the actual application packages, not a separate copy of
unsafe examples. `python scripts/run_sast.py --save-as before` and `--save-as after`
preserve student evidence; the verifier writes to `results/application/current/`.
Bandit runs in quiet mode so its progress display cannot corrupt its JSON report.

The exercise guide retains all ten exercises, including the dedicated cross-user
walkthrough, prompt-template inspection, direct MCP client, direct NeMo worker,
NeMo configuration and file-security repairs. Exercise 7 now demonstrates consent,
limited permissions, replacement, expiry and revocation. The four ecosystem
diagrams match that design. GitHub-hosted CI and a complete student editing
session are not claimed by these local checks.
