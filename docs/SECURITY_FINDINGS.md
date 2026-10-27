# Explain the security findings

Use this reference when filling in [Student evidence](NOTES_TEMPLATE.md). Record the file/line and output you actually observed.

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

## What makes evidence sufficient

- For ownership and approval, include the triggering request, actual returned state, changed server function and a passing regression test. Scanner silence alone is insufficient.
- For scanner findings, record the rule, actual source location and review outcome.
- For delegated access, record the selected permissions and the results of denied writes, expiry, replacement and revocation. Never include raw tokens or provider keys. State whether you used browser consent or temporary automated test grants.
- For NeMo, include input, mode, expected decision, actual decision and stage. Distinguish a policy block from a worker/model failure.

If submitting JSON, use `finding.schema.json` in this directory. It requires `title`, `cwe`, `file`, `line`, `evidence` and `recommendation`. Its `cwe` field contains one identifier such as `CWE-862`; extra fields are not allowed.
