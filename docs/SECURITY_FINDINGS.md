# Explain the security findings

Use this reference when filling in [Student evidence](NOTES_TEMPLATE.md). Follow [Exercise 10](EXERCISES.md#10-fix-unsafe-ticket-imports-and-attachment-downloads) for the scanner steps. Record the file/line and output you actually observed.

**CWE** names a specific weakness. **OWASP** categories group broader risks. The mappings below are teaching classifications, not a claim that a scanner performed a complete OWASP assessment.

## Vulnerabilities in the running application

| Observed behavior | Weakness and OWASP category | Required repair | Evidence after repair |
|---|---|---|---|
| Alice can read or close a ticket belonging to Bob | CWE-862: Missing Authorization; Broken Access Control | Check the authenticated actor against ticket ownership in server policy | Own read works; cross-user read and close tests pass |
| Extra fields such as `approved` are ignored instead of rejected | CWE-20: Improper Input Validation; can contribute to Broken Access Control | Validate the exact schema in both website and server before dispatch | Extra-field/wrong-type tests pass; valid own read still works |
| An AI closure request closes a ticket without human confirmation | CWE-863: Incorrect Authorization; Broken Access Control | Pending approval bound to actor/ticket, expiry, one-use claim, owner/status recheck | Pending ticket stays open; explicit confirmation closes once; expiry/reuse/other-actor tests deny |

Do not report unknown tools, ungranted writes or forged tokens as successful
exploits: the provided authorization mechanism should reject them. Service
unavailability is not evidence of attack prevention. Exercise 7 checks consent,
limited permissions, expiry and revocation as existing infrastructure.

## File operations used by the running website

| Function and entry point | Weakness and OWASP category | Repair |
|---|---|---|
| `tickets/file_imports.py:load_ticket_file`, called by `/tickets/import/` | CWE-502: Deserialization of Untrusted Data; Software and Data Integrity Failures. Reading an attacker-supplied pickle can execute Python before validation. | Accept JSON only and validate exactly the title field. |
| `tickets/attachments.py:open_attachment`, called by `/tickets/<id>/attachments/download/` | CWE-22: Path Traversal; Broken Access Control. A manipulated download name can read outside the selected ticket's attachment folder. | Resolve and confine the path, require the matching attachment record, and retain the shared ticket-owner check. |

These functions are called by real Django views. Demonstrate them using the
normal import and attachment pages, then connect the observed behavior to the
scanner's actual file and line. The pickle test input only prints a marker;
recording that marker proves Python ran during import even if the file's data
was rejected afterward. No network-diagnostic example is part of the application.

## What makes evidence sufficient

- For ownership and approval, include the triggering request, actual returned state, changed server function and a passing regression test. Scanner silence alone is insufficient.
- For file-operation scanner findings, include tool/rule ID, actual source path/line, the unsafe operation and the corresponding safer function. Report remaining Bandit review warnings rather than claiming every report is empty.
- For delegated access, record the selected permissions and the results of denied writes, expiry, replacement and revocation. Never include raw tokens or provider keys. State whether you used browser consent or temporary automated test grants.
- For NeMo, include input, mode, expected decision, actual decision and stage. Distinguish a policy block from a worker/model failure.

If submitting JSON, use `finding.schema.json` in this directory. It requires `title`, `cwe`, `file`, `line`, `evidence` and `recommendation`. Its `cwe` field contains one identifier such as `CWE-862`; extra fields are not allowed.
