# Instructor guide

This workshop teaches students to find and fix security problems in a ticket
system. The system includes an AI assistant, but students can also create and
manage tickets through ordinary forms.

Use [Exercises](EXERCISES.md) for the student instructions. This guide explains
what each activity teaches, what to prepare, and how to judge the results.

## How this follows Session 1

In Session 1, students worked on a chatbot that answers messages. They learned
to defend it against messages that try to make it ignore its instructions or
reveal information.

In Session 2, the assistant can also ask the application to read or change
tickets. That creates new problems: it might read another student's ticket or
close a ticket without asking for confirmation. Blocking suspicious messages
does not solve those problems. The application must check who owns the ticket
and whether the student has confirmed the change.

The lesson is to check an action before carrying it out, even when the request
comes from an AI assistant.

## What students do

1. **Use the ticket system.** Students create tickets for Alice and Bob, then ask
   the assistant to read a ticket after explicitly granting read-only access for 30 minutes. They run tests that repeat these ordinary
   actions. These actions must continue to work after the security repairs.

2. **Inspect structured model output.** Confirm the read grant from Exercise 1 is active; renew it if expired. Students ask Qwen to read their latest ticket,
   inspect the prompt and three JSON responses in Debug, and compare the selected
   ticket with the server result. They locate the response schema in the code and
   distinguish data format rules from permission checks.

3. **Reject invalid requests.** Students find and fix a flaw that lets the
   application accept invalid ticket requests. They check that it rejects those
   requests while continuing to accept valid ones.

4. **Protect each student's tickets.** Students show that Alice can read Bob's
   ticket. They change the code so a student can read or close only their own
   tickets, then test that restriction.

5. **Call the ticket server directly.** Students start the MCP server and use
   the client to discover its actions, read their own ticket and check that
   requests for another student's ticket and read-only writes are refused.

6. **Ask before closing a ticket.** Students show that the application closes a ticket
   immediately. They change it to require the student to confirm first. They also
   check that another person cannot use the confirmation and that it cannot be
   used twice.

7. **Test assistant permissions, expiry and revocation.** Students revoke the
   grant used in Exercises 1–6, verify ordinary tickets still work, then test
   denial and new grants. They try read-only
   and write permissions, expire or revoke a token, and observe that ticket
   pages remain available. Tokens are per user and client.

8. **Run NeMo directly.** Students start the worker from a terminal, send an
   ordinary message and an override request, and inspect the returned decisions.
   They trace standard input/output to the Python code that Django uses.

9. **Configure NeMo.** Students edit a Python rule, add a Colang flow and enable
   it in NeMo's YAML configuration. They restart the application and check that
   the new rule blocks requests for every student's records while allowing a
   student to ask about their own record.


The activities are planned for about **180 minutes**, excluding installation,
discussion and troubleshooting. Allow extra time or assign preparation and
follow-up work if the class period is shorter.

## Terms used in the workshop

- **Ticket server:** the separate Python program that reads and changes ticket
  records for the assistant by calling the shared `tickets/ticket_service.py`.
  Ordinary ticket forms call that module directly, without MCP.
- **MCP:** the protocol the assistant client uses to ask the ticket server which actions
  it supports and to request those actions. The server must check permissions
  even if a caller bypasses the website.
- **NeMo Guardrails:** the software that checks user messages, proposed actions,
  returned data and answers for the workshop's prohibited content. It does not
  decide whether Alice owns Bob's ticket; the application checks ownership.
- **Qwen and Ollama:** Qwen is the local AI model. Ollama is the application that
  runs it. Demo mode uses fixed rules instead of a model, so it needs neither a
  model download nor a provider API key.
- **Bandit and Semgrep:** tools that inspect source code for potentially unsafe
  patterns. Students must still check what each finding means in that code.
- **Assertion:** a specific expectation in an automated test, such as “Alice's
  request for Bob's ticket must be refused.” A failed assertion means the actual
  behavior differed from that expectation.

Introduce a term when it becomes relevant. Do not use the term in place of
explaining what the application or student is doing.

## Prepare before class

Use an unchanged copy of `starter/`. Keep `solution/` as the completed answer key.
If your own application has already been repaired, it will no longer demonstrate the
original problems. Do not reset a student's working copy to recreate them.

Follow the [Codespaces setup guide](GITHUB_CODESPACES_SETUP.md). Then verify the following:

- Signing in opens **Your tickets** at `/tickets/`.
- Alice and Bob can each create and view a ticket using the ordinary ticket form.
- The assistant can read a saved ticket in **Demo** mode.
- For the Qwen activity, Ollama is running, the configured model is installed,
  and the assistant can read a ticket in **Qwen** mode too. Download the model
  before class rather than using class time for installation.

Setup generates Alice's and Bob's login passwords. Save them when they are
printed. These passwords sign users into the website. Assistant access is granted separately through consent. The student guide explains how to recover a forgotten login password.

From `starter/`, with its existing Python environment active, run:

```bash
python manage.py test tests.test_ticket_portal
python manage.py test tests.test_chat_storage
python manage.py test tests.test_prompt_security
```

These tests check ordinary ticket use, assistant requests and protections already
provided by the project. They should pass before students edit the code. Passing
them does not mean the missing ownership and confirmation rules are implemented.

Then run:

```bash
python scripts/healthcheck.py
```

This command starts the actual ticket server and sends it test requests. In its
default mode, it checks that the application still lets Alice read Bob's ticket and
closes tickets without confirmation. It also checks existing protections, such
as refusing writes with a read-only user token. It creates temporary users,
tickets and test grants, leaving browser accounts and consent unchanged.

The command prints a report with a result for each request. In this mode, a
successful run means the starting exercise behaves as intended, **including its
deliberate security flaws**. It does not mean the application is secure.

Give students a copy of [Student evidence](NOTES_TEMPLATE.md) for their notes.
Distribute source files, not your `.env`, `.venv/` or database files.
Those contain installation-specific settings, credentials or data.

## Keep the tests connected to the activity

Students should first see a problem in the application. Next, they run the test
that repeats that particular request. They read what the test expected, change
the relevant code, and run the same test again. They also repeat an ordinary
request to check that their repair did not break it.

For example, Alice reads Bob's ticket in the browser. The matching test expects
the request to be refused. Before repair it reports `PermissionError not raised`:
the code returned the ticket instead of refusing. After the ownership repair,
that same test should pass.

Do not ask students to run the entire test collection before explaining the
behavior being tested. The exercise guide introduces each relevant test beside
its demonstration and explains the printed result.

## Know what each kind of test proves

The focused Python tests use temporary records. Most replace the separate server
connection with a direct call inside the test program and turn off NeMo. Some
also replace the model with a fixed sequence of proposed actions. This lets a
test check one rule without depending on other programs being available.

Those tests are useful, but they cannot prove that a separately running server
will refuse a caller who bypasses the website. The health-check script tests that
connection using the actual MCP server and NeMo software. By default it uses
fixed planning rather than Qwen. Adding `--semantic` also tests the live model
and model-based NeMo decisions.

The exercise guide explains each report entry when students reach that check.
A connection failure is not evidence that an unauthorized request was correctly
refused.

## Use the right checks as students repair the code

Before repairs, the default health check expects the original flaws. While
students are changing validation, ownership and confirmation, use the specific
tests listed in their current exercise.

After the ownership and confirmation repairs are complete, run:

```bash
python scripts/healthcheck.py --secured
```

`--secured` changes the expected behavior: Alice must now be denied access to
Bob's ticket, and closure must require confirmation. Without this option, the
script still expects the original vulnerabilities.

After students finish the repairs, run the final check:

```bash
python scripts/verify_workshop.py --secured
```

This runs the tests, the actual server checks and the code-scanner checks.
Add `--semantic` when also checking live Qwen. Students should record which
commands they ran and what the output actually showed.

## Points to explain during discussion

**A login is not permission to access every ticket.** Signing in identifies Alice.
The application must still check that a requested ticket belongs to her.
Separately, consent lets Alice authorize the assistant to request selected actions
for her account. The MCP server derives Alice's identity from that grant.

**A well-formed request can still be forbidden.** JSON is the text format used for
proposed actions. A request can have all the correct fields and types yet ask to
read Bob's ticket as Alice. Checking the format and checking permission solve
different problems.

**The assistant cannot confirm its own request.** It may ask to close a ticket.
The signed-in user reviews and confirms on the ticket page. The form calls the
shared ticket service directly; MCP provides no confirmation tool. A delegated
permission to request closure is not permission to confirm it.

**A displayed ticket result must reflect the saved data.** Python builds that
result from the server's response. The model's draft answer is available in Debug.
If a ticket was created and a later model request failed, the page must show both
the completed creation and the separate application error.

**NeMo supplements the permission checks.** The starter enables it in Exercise 8; the solution includes it enabled. Blocking an instruction-override attempt does not establish that the
server enforces ticket ownership or asks for confirmation.


## When a student gets stuck

Start with what they were trying to do and what actually happened. Ask for the
exercise step, the request they entered and the complete result or error. If they
used the assistant, also ask whether they selected Demo or Qwen. Then inspect the
relevant Debug entry or test failure together.

Do not treat “it failed” as evidence that a defense worked. A missing package,
unavailable program or model timeout is different from refusing a request because
the user lacks permission. Do not recommend deleting saved credentials, databases
or Python environments as a general troubleshooting step.

For code review, compare the student's changes with
`solution/chatbot/tool_policy.py` and `solution/tickets/ticket_service.py`.
Students can verify their repairs in their own application; they do not need to run
a second website.

The repository also contains a GitHub workflow that runs tests automatically
when changes are pushed. Local results do not prove that this workflow ran;
check the repository's Actions page for its result. State which environments
and model providers were actually demonstrated rather than assuming that a local
success proves Codespaces or Gemini also worked.

All test files now live in `tests/`, grouped by subject. Initial checks cover
ordinary ticket use, chat behavior and the inherited message checks. The three
repair exercises each use one short command for their topic file. NeMo's new
configuration tests intentionally fail until Exercise 9 is completed. The answer
key has the completed rule and configuration; do not copy them into the student
application before the exercise.

### Activate the environment in every exercise terminal

From `starter`, run `source .venv/bin/activate` in the Codespaces terminal. Then use `python ...` for
all workshop commands. Repeat activation in every new terminal.
See [exercise terminal instructions](EXERCISES.md#every-new-terminal-needs-the-workshop-environment).

## Exercise 6 teaching scope

Students add only the two-line closure routing check in `tickets/ticket_service.py:execute`, before `result = dispatch(...)`. `tickets/confirmation.py` supplies pending approval and final-confirmation mechanics. Do not ask students to design ORM queries, locking, expiry or transactions. Demonstrate through Qwen before and after; the human confirms on the ticket page.
