"""User-visible outcomes are built from authorized server data, never model prose."""
def describe(result, tool):
    if "pending_approval" in result:
        return f"Open the ticket page to confirm closure of ticket #{result['ticket_id']}."
    if "tickets" in result:
        tickets = result["tickets"]
        return ("Your tickets: " + "; ".join(
            f"#{t['ticket_id']}: {t['title']} ({t['status']})" for t in tickets)
            if tickets else "You have no tickets yet.")
    if "ticket_id" in result:
        identifier = result["ticket_id"]
        title = result.get("title", "")
        if tool == "create_ticket":
            return f"I've created ticket #{identifier}: {title}. You can open it from Your tickets."
        if tool in {"close_ticket", "confirm_close_ticket"}:
            return f"Ticket #{identifier} is now {result['status']}."
        return f"Ticket #{identifier}: {title}. Its status is {result['status']}."
    raise ValueError("The ticket server returned an unrecognized result.")
