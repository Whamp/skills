---
name: integration-testing
description: Companion to `tdd` when the test you need crosses boundaries. Use when testing API, database, service, filesystem, queue, or contract boundaries; when deciding what should be real vs mocked; or when setting up test databases, containers, and other integration environments. Covers the test pyramid, test containers, contract testing, and flaky test prevention.
disable-model-invocation: true
---

# Integration Testing

Unit tests prove components work alone. Integration tests prove they work together.

> **Scope:** Testing across boundaries (API, database, services). Not unit testing (see language-specific testing experts), TDD workflow (see test-driven-development), or fuzz testing (see fuzzing).

## Test Pyramid

```text
         /  E2E  \        Few, slow, expensive, high confidence
        /─────────\
       / Integration\     Moderate count, test boundaries
      /──────────────\
     /   Unit Tests    \   Many, fast, cheap, focused
    /───────────────────\
```

| Level | Tests | Speed | What It Catches |
| ------- | ------- | ------- | ----------------- |
| **Unit** | Hundreds | ms each | Logic errors in isolated functions |
| **Integration** | Tens | seconds each | Boundary mismatches, serialization, SQL, config |
| **E2E** | Few | minutes each | Full user flow failures, deployment issues |

**Prefer** more unit tests, fewer integration tests, fewest E2E. But don't skip integration tests — they catch what unit tests structurally cannot.

## What to Test at Each Boundary

| Boundary | Test Strategy | Mock? |
| ---------- | -------------- | ------- |
| **Database** | Real DB (testcontainers or in-memory) | No — SQL bugs hide behind mocks |
| **HTTP API** | Real server (supertest, httptest) | No — test serialization + routing |
| **External service** | Mock or record/replay (msw, wiremock) | Yes — you don't own it |
| **File system** | Temp directory, cleanup after | No — real FS behavior matters |
| **Message queue** | Real broker or in-memory fake | Depends on complexity |

**Do** test against real databases — mock repositories miss SQL bugs, constraint violations, and migration issues.

**Don't** mock everything — an integration test that mocks all dependencies is a unit test with extra steps.

## Test Environment Setup

### Testcontainers (Docker-based)

```python
# Python: testcontainers
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="session")
def db():
    with PostgresContainer("postgres:16") as pg:
        engine = create_engine(pg.get_connection_url())
        run_migrations(engine)
        yield engine
```

```go
// Go: testcontainers-go
func TestWithPostgres(t *testing.T) {
    ctx := context.Background()
    pg, _ := postgres.Run(ctx, "postgres:16",
        postgres.WithDatabase("testdb"),
    )
    defer pg.Terminate(ctx)
    connStr, _ := pg.ConnectionString(ctx)
    // Run tests against real Postgres
}
```

### Transaction Rollback (fast per-test isolation)

```python
@pytest.fixture(autouse=True)
def db_session(db):
    conn = db.connect()
    tx = conn.begin()
    yield conn
    tx.rollback()  # Each test starts clean, no data leaks
```

## Contract Testing

Verify that service A's expectations match service B's implementation.

```text
Consumer (client)  →  Contract  ←  Provider (server)
                    (shared spec)
```

```typescript
// Consumer-side: define what you expect from the provider
const userContract = {
    endpoint: "GET /api/users/:id",
    response: {
        status: 200,
        body: {
            id: Matchers.string(),
            email: Matchers.email(),
            name: Matchers.string(),
            // Consumer doesn't care about fields it doesn't use
        },
    },
};

// Provider-side: verify the contract is satisfied
// Run the provider's actual API against the contract
```

**Tools:** Pact (multi-language), Schemathesis (OpenAPI), dredd (API Blueprint).

**Do** use contract tests between teams — they catch breaking API changes before deployment.

## Flaky Test Prevention

| Cause | Fix |
| ------- | ----- |
| **Shared state** | Isolate per test (transactions, temp dirs, unique IDs) |
| **Time dependence** | Inject clock, freeze time (`freezegun`, `faketime`) |
| **Network calls** | Mock external services (msw, wiremock, httpretty) |
| **Race conditions** | Don't use `sleep()` — use retry/poll with timeout |
| **Order dependence** | Randomize test order, fix shared setup |
| **Port conflicts** | Use random ports or testcontainers |

**Do** run tests in random order to catch hidden dependencies.

**Don't** use `time.Sleep` to wait for async operations — poll with timeout:

```go
// Bad: time.Sleep(2 * time.Second)
// Good: poll until condition or timeout
require.Eventually(t, func() bool {
    return checkCondition()
}, 5*time.Second, 100*time.Millisecond)
```

## Do / Don't / Prefer

**Do** clean up test data after each test. Leaked state causes flaky tests.

**Do** test error paths — what happens when the database is down, the API returns 500?

**Don't** write integration tests for pure logic — use unit tests for that.

**Don't** share test databases between parallel test suites without isolation.

**Prefer** testcontainers over shared test databases — each test run gets a fresh instance.

**Prefer** API-level integration tests over UI-level E2E for backend services.

## References

- [references/patterns.md](references/patterns.md) — HTTP API testing, database testing, async testing, and CI patterns per language
