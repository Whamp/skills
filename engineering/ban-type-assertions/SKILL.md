---
name: ban-type-assertions
description: "Ban `as` type assertions via the native oxlint `typescript/consistent-type-assertions` rule (`assertionStyle: 'never'`), replacing them with compiler-verified type-safe alternatives. Use when enabling the assertion ban in a project or fixing violations in an existing one."
disable-model-invocation: true
---

# Ban Type Assertions

Enable `typescript/consistent-type-assertions` with `assertionStyle: 'never'`
(**native oxlint, v1.44.0+**) and replace all `as X` / `<T>x` casts with patterns
the compiler can verify. `as const` is **preserved** — the ban is surgical: it
targets real casts, not literal narrowing.

## Core Philosophy

> Pick the strictly correct path, not the simpler one.

Every `as` assertion is a spot where the developer told the compiler "trust me."
The goal is to make the compiler *verify* instead. If you replace `as Foo` with a
type guard that is equally unverified, you have not improved anything — you have
just moved the assertion.

## Quick Reference

- Rule: `typescript/consistent-type-assertions`
- Config: `{ assertionStyle: 'never' }`
- Enforcement: **native oxlint** (v1.44.0+) — no jsPlugins, no eslint sliver
  (per the `typescript.md` standard, decision #6). Part of the shared
  `.oxlintrc.json`.

## Workflow

### 1. Enable the Rule

Add to the project's `.oxlintrc.json` (oxlint flat config):

```jsonc
{
  "rules": {
    "typescript/consistent-type-assertions": ["error", { "assertionStyle": "never" }]
  }
}
```

Run type-aware: `npx oxlint --type-aware .` (the `oxlint-tsgolint` package drives
the real TypeScript compiler; needs TypeScript 7.0+).

### 2. Enumerate Violations

```bash
npx oxlint --type-aware . 2>&1 | grep "consistent-type-assertions"
```

Group violations by file and pattern before fixing.

### 3. Research Before Fixing

Before writing any replacement code:

1. **Check for existing zod schemas** — grep for `Schema` alongside the type name
   across the project.
2. **Check if schemas exist but aren't exported** — if so, export them rather than
   creating new ones.
3. **Check for duplicate types/interfaces** — consolidate into a shared schemas
   module if found.
4. **Understand the data flow** — is this a parse boundary (external data), a
   narrowing site (union type), or a library type gap?

### 4. Fix Violations Using the Pattern Hierarchy

#### Tier 1: Zod Parsing (for external data boundaries)

Use for any data entering the system from JSON, disk, network, IPC, etc. This
gives **runtime validation**, not just a type annotation.

```typescript
// BAD
const data = JSON.parse(raw) as MyType;

// GOOD
const data = MySchema.parse(JSON.parse(raw));
```

Use `safeParse` when you need to handle errors gracefully (e.g., returning an
error response with context like a request id):

```typescript
// BAD: throws before you can extract the request id
const request = RequestSchema.parse(JSON.parse(raw));

// GOOD: safeParse lets you return a proper error
const parsed = RequestSchema.safeParse(JSON.parse(raw));
if (!parsed.success) {
  return errorResponse(rawObj?.id ?? null, INVALID_PARAMS, parsed.error.message);
}
const request = parsed.data;
```

#### Tier 2: Control Flow Narrowing (for union types)

Use `switch`, `in`, `instanceof`, or discriminated unions:

```typescript
// BAD
(error as NodeJS.ErrnoException).code

// GOOD
if (error instanceof Error && 'code' in error) {
  const code = error.code;
}
```

```typescript
// BAD
if (METHODS.has(method as Method)) { ... }

// GOOD: switch narrows exhaustively
switch (method) {
  case 'foo':
  case 'bar':
    return handle(method); // narrowed
}
```

#### Tier 3: oxlint-disable with Justification (last resort)

Only for genuinely unavoidable cases (library type gaps, generic parameters that
can't be inferred). Always explain *why*:

```typescript
// oxlint-disable-next-line typescript/consistent-type-assertions -- ws library types require a generic parameter
ws.on('message', handler);
```

#### Anti-Pattern: Type Guards That Are Disguised Assertions

```typescript
// NOT an improvement -- checks shape but not content
function isDaemonRequest(x: unknown): x is DaemonRequest {
  return typeof x === 'object' && x !== null && 'method' in x;
}
```

A zod schema validates values. A type guard like this is an unverified assertion
with extra steps. Only use type guards when the narrowing logic is truly
sufficient.

### 5. Use Strict Schemas, Not Permissive Ones

When a schema exists (e.g., `SessionSettingsSchema`), use it strictly rather than
`z.record(z.unknown())`. This ensures forward compatibility — if fields are
removed in a migration, stale data gets cleaned on read.

```typescript
// BAD: accepts anything
const settings = z.record(z.unknown()).parse(raw);

// GOOD: validates against the real shape
const settings = SessionSettingsSchema.parse(raw);
```

### 6. Fix Test Mocks to Match Schemas

Once you replace `as X` with `.parse()`, test mocks that relied on the assertion
will fail validation. Fix the mocks — do not disable the rule in tests.

Create helper functions to centralize valid test fixtures:

```typescript
function mockSessionSummary(
  overrides?: Partial<SessionSummaryEvent>,
): SessionSummaryEvent {
  return {
    type: 'session_start',
    id: 'test-id',
    title: 'Test Session',
    owner: 'test-owner',
    ...overrides,
  };
}
```

### 7. Parse at the Boundary, Inside Error Handling

Make sure parsing happens where failures produce proper error responses, not
unhandled exceptions:

```typescript
// BAD: parse outside try/catch -- if it throws, you lose context
const request = RequestSchema.parse(data);
try { handle(request); } catch { ... }

// GOOD: safeParse before try, handle error with context
const parsed = RequestSchema.safeParse(data);
if (!parsed.success) {
  return errorResponse(rawData?.id ?? null, INVALID_PARAMS, parsed.error.message);
}
try { handle(parsed.data); } catch { ... }
```

## Verification

```bash
npx oxlint --type-aware .   # lint — the native rule fires
npx tsc --noEmit            # typecheck
npm test                    # tests — mocks must match schemas
# knip is opt-in (typescript.md [TS-43]) — run it for larger projects / monorepos
```

## Reminders

- Exported enums live in `enums.ts` (`@factory/enum-file-organization` /
  `structure.md` [ST-01]); for string-union data at a boundary, use a schema +
  enum, not an `as` cast.
- Prefer fixing mocks over disabling the rule; a scoped `oxlint-disable` is the
  last-resort escape hatch — never a blanket disable.
- This rule bans `as X` / `<T>x`; `as const` is unaffected. Non-null `!`
  assertions are a separate, softer review policy (see `typescript.md` [TS-17]).

---

> **Adaptation note (2026-07, decision #11).** Derived from Factory-AI's
> `ban-type-assertions` skill. Step 1 was rewritten from the original
> `@typescript-eslint/consistent-type-assertions` in `packages/<name>/.eslintrc.js`
> to native oxlint (decision #6: no eslint sliver). The original §6 "Promote
> Shared Schemas to `@factory/common`" (Factory monorepo: subpath `package.json`
> exports + `no-barrel-files` + repo-root `npm run knip`) was pruned — it does not
> apply to this consumer stack. The portable core (philosophy, pattern hierarchy,
> strict schemas, test-mock fixing, parse-at-boundary) is retained.
