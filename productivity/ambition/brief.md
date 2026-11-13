# Brief check

A brief is a task written for another agent that starts with none of this conversation. That agent sees only the brief, the repository, and its own tools. A brief is usually long and its scope is already decided, so what it lacks is what the other agent cannot see. This type keeps the scope fixed and makes the brief work **cold**.

Read the brief the way that agent would, and check it against the real code, files, docs, and logs.

## Questions

1. What can the other agent not resolve by itself? Look for references that only this conversation explains ("the bug we found", "option B", "as discussed"), decisions the brief relies on without stating them, and files, commands, or setup it assumes.
2. Which paths, symbols, line numbers, commands, and versions in the brief are wrong or out of date against the repository as it is now? Give the correct value for each.
3. How will the other agent know it is done? When the brief does not say, find the real check here: a test, a command, an output, a file to compare against.

## Rules for the rewrite

- Fix only those gaps: put the missing facts in, correct what is wrong, and add the check from question 3 when it was missing.
- Keep the brief's goal, scope, order, wording, and length as close to the original as you can.
- When nothing needs fixing, return the brief unchanged and say so.

These rules replace the "change the kind of work" rule in the main file. To raise a brief's ambition as well, run a second type on it first, then run this check on the result.
