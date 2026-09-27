---
name: model-routing
description: Select delegated models or recover failed routes while preserving permissions, capacity limits, and review independence.
---

# Model routing

The parent selects each child's model; children need not inherit the routing policy.

1. Read the caller's private routing profile. Keep **permission**, **availability**, and **task fit** separate. A configured or catalog-listed model is not spending authorization. Obtain explicit user-message approval wherever the profile requires it.
2. Read the caller's role configuration when selecting a delegated model. Resolve the requested role from that file rather than a copied prompt table or a remembered assignment. Verify the exact selector and pass it explicitly at launch. Keep that choice unless unavailable or overridden by the caller's spending priorities. If no workflow role matches the task, use the caller's fallback guidance rather than inventing defaults.
3. Before substantial delegation, check or reuse recent capacity observations for candidate pools. Respect all limiting windows, concurrency, aggregate context budgets, and reserved services. Unknown telemetry permits bounded use of an authorized route; it neither proves headroom nor clears known exhaustion. Keep provider/account pools separate from model families.
4. When a route fails, use the caller's ordinary-work or demanding-review fallback guidance. Skip exhausted pools, including their other models. Preserve required capabilities, context, tools, runtime, write authority, and review axes. Distinguish missing child tools from model unavailability. Retain completed work and report substitutions. Ask when no permitted capable alternative satisfies the task; never activate paid overage or cross approval boundaries to recover.
5. When independent review is required, preserve the required family coverage. Different providers serving the same family do not supply independence. Do not replace the sole independent reviewer with the implementer's family.

For Pstack roles, read `pstack/models.json` under `PI_CODING_AGENT_DIR`, or `~/.pi/agent` when unset. Read the requested entry from the v2 `roles` map, regardless of Poteto Mode or `skillsEnabled`. Preserve selector suffixes, list order, and duplicate entries. Follow the workflow's role cardinality: `single` launches one child, `repeat` reuses one selector, `fanout` launches one child per list entry, and `pick-one` chooses one listed selector. A missing role, `inherit-parent`, or `auto` uses the parent model. Resolve that model explicitly before launch. If the JSON file is absent, check `pstack-models.md` in the same agent directory before treating the config as missing. A missing config uses Pstack's inherit-parent default. For legacy or invalid config, inspect `/pstack status` and resolve diagnostics before delegation rather than guessing or rewriting assignments.

Before selecting a Cursor route, read [the Cursor runtime reference](CURSOR-SUBAGENTS.md).

Complete when each child has an explicit eligible model and the required coverage is preserved, or the unmet requirement is reported.
