---
name: ambition
description: Rewrite a task, plan request, or subagent brief into a more ambitious version, grounded in the real material, for you to read before anything runs.
disable-model-invocation: true
license: MIT
---

# Ambition

People ask for what they believe is possible, and that belief lags what a model with a computer can do. A request therefore tends to understate what the user wants. Specific, hard goals produce better work than "do your best". A stretch attempt that reports plainly where it fell short is a good result.

This skill returns a **rewrite**: the user's request restated at the ambition it deserves, ready for the user to read, edit, and send. Your whole job is to read and rewrite. The work itself starts when the user sends the rewrite.

**The request** is the text given with the invocation. With no text, it is the task in progress in this conversation, including the feedback the user has given on work already done. It may be a task, a request for a plan, or a brief for another agent.

## Steps

### 1. Ground

Before you form a view, and without asking the user anything, read the code, files, docs, logs, and data the request touches. Where the conversation holds a summary and its source is reachable, open the source; a screenshot counts as a source. Search the current checkout and the paths the request names, give any command that may be slow a short timeout, and narrow a search that times out. Stop reading when more would leave your answers as they are.

**Complete when** you can name the files, components, commands, data, and existing checks the request touches, and you know which raw material is out of reach and what access would open it. Name that material in your answers.

### 2. Pick the type

First test for a **right-sized** request: a mechanical edit, a lookup, or a step in a plan the user already approved, where an expert would do exactly what is asked. For a right-sized request, say so in one line, add any fact from step 1 that the work would trip over, return the request unchanged in the fenced block, and end your turn.

Otherwise pick from this table:

| What the request shows | Type | Read |
| --- | --- | --- |
| It is one instance of work that will come back, or a deliverable that exists to drive a decision or to keep something true | Altitude | [altitude.md](altitude.md) |
| The quality of this one piece of work is the point, and an expert would judge it | Depth | [depth.md](depth.md) |
| The work is framed inside one field, and the stakes justify more viewpoints | Range | [range.md](range.md) |
| It is a brief for an agent that starts without this conversation | Brief check | [brief.md](brief.md) |

The user may name the type. Otherwise pick the one type the request needs most, and add a second only when the request clearly calls for both. When two types fit equally, use Depth.

**Complete when** you have stated in one line either that the request is right-sized, or the type and the signal for it, and you have read that type's file.

### 3. Answer the type's questions

Answer each numbered question from the type's file in a few lines, starting each answer with its number. Use concrete facts from step 1: file names, counts, real names of components, and commands and tools that exist here.

### 4. Write the rewrite

- Keep the user's goal and voice. Write it as the user's own request, ready to send as is.
- Put the concrete facts from your answers into it.
- For Altitude, Depth, and Range, change the kind of work asked for: its outcome, its methods, or its fields. Keep the amount of same-kind work where the user set it.
- Name the **outside judge**: what, other than the user or the agent doing the work, will show the result is right. Prefer a check the agent can run.
- Leave open the choices that belong to the user. When there are any, list them at the end of the rewrite as questions.

When the rewrite calls for a crew of agents or a reviewer on another model, or the user wants the research kept out of this thread, read [delegation.md](delegation.md).

### 5. Return

Give the type line, then the numbered answers, then the complete rewrite in one fenced `text` block as the last thing in your reply. End your turn there, with every project file as you found it.

**Complete when**, for a rewrite, a reader who has seen only the fenced block could send it and get the more ambitious work.

## Sources

The types and the Depth questions come from Felix Rieseberg's [How to be more ambitious](https://felixrieseberg.com/how-to-be-more-ambitious-a-tutorial-for-humans-with-models/). The read-first rule, the rewrite rules, and the brief check adapt Nico Bailon's [pi-better](https://github.com/nicobailon/pi-better).
