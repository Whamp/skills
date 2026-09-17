# Routing cases

Use these scenarios to check policy changes manually, not as model evaluation results. The Cursor approval cases assume a caller profile that permits Grok and Composer but reserves other Cursor API models for explicitly approved Fable use.

| Scenario | Expected outcome |
| --- | --- |
| ZAI is near-exhausted, but Codex is protected for later work | Treat ZAI as eligible while it is not exhausted: use `zai/glm-5.3-flash:max` for routine work and `zai/glm-5.3:max` for a hard review rather than spending the protected Codex pool. |
| A local inference service is under test, reserved, or unavailable | Exclude the local route even if its endpoint responds; select another eligible route. |
| Direct xAI is exhausted but Cursor Grok remains usable | Treat direct xAI and Cursor Models as distinct pools. Use authorized Cursor Grok if available, while counting both as the same model family for review independence. |
| A skill suggests Cursor API Fable but no user message approves it | Exclude Fable. A skill, catalog entry, role table, or inferred difficulty cannot authorize the run. |
| A user message grants Fable permission for a scoped use | Use Fable only for the approved scope and record that message; do not extend permission to other tasks, fallbacks, wrappers, or resumed children. |
| A Cursor Gemini route is proposed as an automatic fallback | Exclude it: Cursor API models outside the Grok and Composer routes need explicit user-message permission. |
| An authorized Kimi Code route is active but usage telemetry is missing | Keep it eligible for bounded use, preserve source-reported windows when available, and record capacity as unknown rather than assuming headroom or exhaustion. |
| Kimi Code is reported discontinued | Stop assigning Kimi Code and exclude its route. |
| A reviewer role is missing a required tool | Treat this as a tool-profile failure, not model unavailability. Use a compatible supported role without switching runtimes. |
| Grok is unavailable for a required independent review axis | Preserve the axis with an eligible capable GLM or Kimi route, if authorized; do not make Grok mandatory. |
| GLM-5.3-Flash and GLM-5.3 are proposed as independent reviewers | Count them as one GLM family and add a different eligible family for independent coverage. |
| The parent can synthesize completed reviews without another child | Do not require a Sol child solely for synthesis; preserve evidence and disagreements while using the parent or another eligible synthesis route. |
