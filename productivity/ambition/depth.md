# Depth

Depth asks for the work the way a field-leading professional would do it: with their tools, techniques, and raw material, pushed until even they might learn something from the result. The aim is a **deeper** version of the task, not a bigger one.

## Questions

1. What would a top professional in this field do here that the request does not ask for?
2. What is the rawest material they would start from, instead of what has already been digested for the user?
3. Which specific methods and tools would they use?
4. What, other than the user or the agent, would show the result is right?

## Moves for the rewrite

Use the moves that fit the request. Each one changes how the work is done. Anything new the work builds, such as a model or a simulation, serves the deliverable the user asked for.

- **Raw material.** Ask for the work to start from the thing itself, produced or fetched fresh: real output, real failures, real records. Code and summaries that describe the thing come second.
- **Instruments.** Insist on the expert's instrument by name where the plain version reaches for a lighter one: a database and a statistical model in place of a table read by eye, a profiler in place of reading the code for slow spots. A change of vocabulary alone leaves the methods where they were, so name the method and the tool.
- **An unreasonable target.** Pick a specific target far past what the request asks: asked for a 5-second page load, write 200 milliseconds. Where the request sets no measure, name the one an expert would use.
- **Test what is believed.** Find the beliefs the request treats as settled, and ask for an adversarial check of each one against the raw material: "We believe churn is an onboarding problem. Try to reproduce that from the raw data."
- **New knowledge.** Once the work is inside the raw material, ask for what nobody knows yet, and for proof on material the work has not seen: "Build a simulation of our customers that reproduces the last year from our logs. Then find the earliest signal of churn we don't know about yet, and show it predicts on data it has not seen."
- **Outside judge.** Make the answer to question 4 a tool the agent can run for immediate feedback: a test, a benchmark, a held-out dataset, a comparison against the real output. A model's opinion of its own work does not count as the judge.
