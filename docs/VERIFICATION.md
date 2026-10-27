# Session 2 verification

The file-handling exercises and implementation have been separated into Session 4.
Session 2 checks cover the ticket portal, model proposals, validation, ownership,
human confirmation, delegated MCP authorization and NeMo guardrails.

From `starter` or `solution`, activate that folder's environment, then run:

```bash
python scripts/verify_workshop.py
```

After completing the starter's repairs, add `--secured`. Add `--semantic` only
when Ollama/Qwen is running. Tests use temporary data; the integration check
uses disposable users, grants and a temporary database. Neither issues grants
for real browser users. Scanner output still requires review.

Existing installations should run `python manage.py migrate` after stopping
the website. The forward migration removes the retired file metadata model;
tickets, accounts, conversations, grants and approvals are retained. The original
application and its local file data were copied into Session 4 before removal.
