# Theme configuration

Set `CHATBOT_THEME_FILE` in the application's `.env` to a JSON path relative to
`starter/` (or `solution/`), then restart Django. Existing choices are preserved.

- `themes/utep_student_helper.json`: the UTEP example scenario.
- `themes/support_desk.json`: a workplace IT service desk example.

The selected file controls assistant name, role, scope, topic vocabulary and mock
responses. Its `ticket_portal` section controls portal title/subtitle, greeting,
chat introduction, placeholder, example buttons, demo request keywords and fallback
response. Shared templates and JavaScript use those values; security checks and
permission rules remain independent of the scenario.

Generic defaults apply when an older theme has no `ticket_portal` section.
Changing a theme does not rename Python packages, tool names or authorization IDs.
