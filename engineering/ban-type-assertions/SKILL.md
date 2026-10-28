---
name: ban-type-assertions
description: Enable the native Oxlint assertion ban and replace casts with checked types and boundary validation.
disable-model-invocation: true
---

# Ban Type Assertions

Apply this stricter policy when requested; it is not a claim about every project's defaults. Replace `as T` and `<T>value` with evidence the compiler or a runtime validator checks. Keep `as const`; non-null `!` assertions follow the project's separate policy.

## 1. Inspect and enable

Read the affected packages, lint/compiler configuration, scripts, schemas and callers. Group cast sites by external-data boundary, internal narrowing, literal construction or library typing gap. Find the existing contract owner, including unexported schemas and duplicate definitions, before creating another contract. Share or export the authoritative definition when needed; preserve the project's module and file-layout rules. For string-union data at a boundary, use a schema plus an enum. Where ST-01 applies, put exported enums in `enums.ts`.

Enable this native rule in the existing Oxlint configuration without replacing unrelated settings or weakening test coverage:

```json
{
  "rules": {
    "typescript/consistent-type-assertions": ["error", { "assertionStyle": "never" }]
  }
}
```

The [native rule](https://oxc.rs/docs/guide/usage/linter/rules/typescript/consistent-type-assertions.html) is available from Oxlint 1.44.0. It is syntax-based: no ESLint bridge, custom plugin or type-aware backend is needed for this rule. Retain the project's type-aware gate for its other rules; that mode needs `oxlint-tsgolint`.

**Complete when:** the rule runs on the affected source and tests, and the cast inventory identifies each site's contract and data flow.

## 2. Replace casts at their cause

| Site | Replacement and evidence |
| --- | --- |
| External JSON, disk, network or IPC input | Parse with the existing schema system, such as Zod. Reuse the actual domain schema and derive its type rather than maintaining a parallel interface or permissive dictionary. Preserve its defaults, limits and unknown-key policy: stripping keys and rejecting them are different contracts. |
| Internal union or caught error | Use discriminants, exhaustive branches, `in` or `instanceof` to establish the required type. A user-defined predicate is trustworthy only when its checks establish every property and value it claims; checking that one key exists is not validation of a whole request. |
| Locally constructed value | Let inference work, use a type annotation, or use `satisfies` to check compatibility without asserting it. Keep literal narrowing where it is intentional. |
| Library or generic mismatch | First try correct generic arguments, a typed boundary or a compiler-checked alternative. A declaration gap is not proof that a cast is necessary. |

At input boundaries, handle malformed syntax as well as schema rejection. Use `safeParse` with an explicit failure branch, or catch parsing failures where the existing error response is built. Preserve error codes, causes and request identifiers; extract an identifier through checked envelope data, not an assertion or optional chaining on an unvalidated value.

When validation exposes invalid test mocks, fix their data. Put repeated valid fixture construction in a typed helper and retain valid overrides; do not loosen the schema or exempt tests to keep old mocks passing.

**Complete when:** replacements preserve successful behavior and error contracts, reject invalid boundary input, and leave no unchecked substitute for the removed cast.

## 3. Verify and account for exceptions

Run the repository's affected-package lint, strict typecheck and tests. Where these are the configured commands:

```sh
npx oxlint .
npx tsc --noEmit
npm test
```

Use `oxlint --type-aware .` when required by the project's other rules. Check runtime rejection and error responses, schema defaults/key handling, valid fixtures and downstream consumers—not just compilation. Consider Knip for larger projects or monorepos when the project opts into that check.

If a cast is genuinely unavoidable, state the established invariant and why the compiler cannot express it. Limit any justified `oxlint-disable-next-line typescript/consistent-type-assertions` to the actual assertion, with the project's required safety rationale. A clean lint result from disabling the rule is not type-safety evidence; broad or test-wide suppression is not a fix.

**Complete when:** affected checks pass, or each blocked check is reported; every remaining cast has a specific justification and scope; and the final report identifies changed contracts, verification results and unresolved risks.

## Source credit

Newly written from this skill's maintained Oxlint workflow and the ideas in Factory's [ban-type-assertions](https://github.com/Factory-AI/factory-plugins/tree/master/plugins/typescript/skills/ban-type-assertions). The earlier adaptation replaced Factory's ESLint setup and removed its monorepo-specific instructions; this version retains that distinction without copying its procedure or examples.
