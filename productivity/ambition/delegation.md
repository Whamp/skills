# Delegation

A rewrite names real tools, so it should name the way this harness runs other agents. Look at your own tool list and use the first row that matches.

| You have | Crew | Reviewer on another model |
| --- | --- | --- |
| T3 Code's `delegate_task` and `orchestrator_capabilities` tools (the names may carry a prefix) | One child per field; each child starts with only its task text | A child on a different provider's model; when the rewrite asks for this reviewer, call `orchestrator_capabilities` once so that it names a real provider and model |
| A native subagent tool only | One subagent per field | Unavailable: every subagent shares your provider, so the outside judge must be a check the agent can run |
| Neither | The fields run one after another in a single thread | Unavailable, as above |

## What the rewrite says

- **Crew.** Ask for each field's work as a separate agent task that states the field's method, its raw material, and the finding to return. Ask for one agent to combine the results.
- **Reviewer.** A check the agent can run stays the first choice for the outside judge. Where only a reading can judge the result, ask for a review by a model from a different provider, and for that reviewer to receive the raw material and the result, without the working agent's own summary of it.
- **Cold starts.** A child starts without this conversation. Write each delegated task in the rewrite so that it holds up against the three questions in [brief.md](brief.md): it explains everything itself, its names are correct, and it states its check. Those questions need no separate numbered answers here.
- **Cost.** State the number of agents and models the rewrite asks for, so the user sees the spend before sending it.

## Keeping the research out of this thread

Steps 1 to 4 can run in a child, so that this thread receives only the answers and the rewrite. Do this when the user asks for it and the request stands alone, because a child cannot see this conversation. Give the child the request, the paths it touches, and the steps of this skill, and tell it to read and rewrite only. When the request is the task in progress, do the steps here: only this thread holds that conversation.
