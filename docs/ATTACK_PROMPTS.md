# Additional ticket requests to try

Complete Exercise 3 in [Exercises](EXERCISES.md) first. These requests check other
invalid inputs after you have added the input checks.

In Alice's assistant page, keep **Qwen** selected and enable **Debug**. Copy each example
into **Test a ticket request**, then click **Submit test request**. Record what
the application returns and whether it matches the expected result below.

## A ticket number written as text

Replace `123` with Alice's ticket number, keeping the quotation marks:

```json
{"tool":"get_ticket","arguments":{"ticket_id":"123"}}
```

Expect refusal. The number must be an integer, without quotation marks. The
ticket server already refuses this input, so also run the test in Exercise 3:
it checks the website code directly.

## An attempt to set another student as owner

```json
{"tool":"create_ticket","arguments":{"title":"Test request","owner":"bob"}}
```

Expect refusal because `owner` is not an allowed input field. The application
uses the signed-in student as owner; the request cannot choose someone else.

## An action the application does not offer

```json
{"tool":"run_shell","arguments":{"command":"echo test"}}
```

Expect refusal. The assistant may only request the defined ticket actions.
It must not execute this command.

## Text that is not a JSON request

```text
not json
```

Expect refusal because this box requires a JSON request. Ordinary conversation
belongs in the assistant's message box.

These refusals should leave ticket records unchanged. If you see a connection
error instead, the application did not complete the test; that error does not
show that it correctly refused the input.
