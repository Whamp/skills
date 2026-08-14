# Delegated Model Work

This context names the roles and reasons used when agent skills delegate coding work across model families.

## Language

**Model-family diversification**:
Deliberately assigning a task to a different model family to obtain independently shaped reasoning and expose assumptions shared by the primary models.
_Avoid_: Model variety, second opinion

**Grok worker**:
An implementation or debugging delegate selected for model-family diversification.
_Avoid_: Grok reviewer, Grok launcher, generic subagent

**Delivery owner**:
The delegating agent that remains accountable for inspecting and verifying a worker's changes, completing delivery, and reporting the result.
_Avoid_: Supervisor, orchestrator

**Candidate change**:
A change produced by a worker that remains incomplete until the delivery owner has inspected and verified it.
_Avoid_: Completed work, delivered change
