# Integration Testing Patterns

Per-language patterns for HTTP API testing, database testing, and async testing. Strategy and flaky test prevention are in the SKILL.md.

## HTTP API Testing

### TypeScript (supertest + vitest)

```typescript
import { describe, it, expect, beforeAll, afterAll } from "vitest";
import request from "supertest";
import { app } from "../src/app";

describe("POST /api/users", () => {
    it("creates a user and returns 201", async () => {
        const res = await request(app)
            .post("/api/users")
            .send({ email: "test@example.com", name: "Test User" })
            .expect(201);

        expect(res.body).toMatchObject({
            id: expect.any(String),
            email: "test@example.com",
        });
    });

    it("returns 422 with validation errors for invalid input", async () => {
        const res = await request(app)
            .post("/api/users")
            .send({ email: "not-an-email" })
            .expect(422);

        expect(res.body.errors).toContainEqual(
            expect.objectContaining({ field: "email" })
        );
    });

    it("returns 409 for duplicate email", async () => {
        await request(app).post("/api/users")
            .send({ email: "dupe@example.com", name: "First" });

        await request(app).post("/api/users")
            .send({ email: "dupe@example.com", name: "Second" })
            .expect(409);
    });
});
```

### Go (httptest)

```go
func TestCreateUser(t *testing.T) {
    srv := setupTestServer(t)  // Creates server with test DB

    body := `{"email": "test@example.com", "name": "Test"}`
    req := httptest.NewRequest("POST", "/api/users", strings.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    w := httptest.NewRecorder()

    srv.ServeHTTP(w, req)

    assert.Equal(t, 201, w.Code)

    var resp map[string]any
    json.Unmarshal(w.Body.Bytes(), &resp)
    assert.Equal(t, "test@example.com", resp["email"])
    assert.NotEmpty(t, resp["id"])
}
```

### Python (pytest + httpx)

```python
import pytest
from httpx import AsyncClient

@pytest.fixture
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

async def test_create_user(client):
    resp = await client.post("/api/users", json={
        "email": "test@example.com",
        "name": "Test User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

async def test_validation_error(client):
    resp = await client.post("/api/users", json={"email": "bad"})
    assert resp.status_code == 422
    assert any(e["field"] == "email" for e in resp.json()["errors"])
```

## Database Testing

### Transaction Isolation Pattern

Each test runs in a transaction that rolls back — fast, no cleanup needed.

```python
# pytest fixture: auto-rollback per test
@pytest.fixture(autouse=True)
async def db_session(engine):
    async with engine.connect() as conn:
        tx = await conn.begin()
        yield conn
        await tx.rollback()
```

```go
// Go: transaction per test
func withTestTx(t *testing.T, db *sql.DB, fn func(tx *sql.Tx)) {
    tx, err := db.Begin()
    require.NoError(t, err)
    defer tx.Rollback()
    fn(tx)
}
```

### Migration Testing

Test that migrations run cleanly in both directions:

```bash
# Apply all migrations
migrate up

# Verify schema matches expectations
# Run integration tests

# Roll back last migration
migrate down 1

# Re-apply — verify idempotent
migrate up
```

**Do** test rollback migrations — they'll fail in production if untested.

## Async / Event Testing

Test event-driven systems by consuming events with a test subscriber.

```python
# Test that placing an order publishes an event
async def test_order_emits_event(client, event_bus):
    events = []
    event_bus.subscribe("order.placed", lambda e: events.append(e))

    await client.post("/api/orders", json={"items": [...]})

    # Poll — don't sleep
    for _ in range(50):
        if events:
            break
        await asyncio.sleep(0.1)

    assert len(events) == 1
    assert events[0]["order_id"] is not None
```

```go
// Go: channel-based event assertion
func TestOrderEvent(t *testing.T) {
    eventCh := make(chan Event, 1)
    bus.Subscribe("order.placed", func(e Event) { eventCh <- e })

    // Place order...

    select {
    case event := <-eventCh:
        assert.Equal(t, "order.placed", event.Type)
    case <-time.After(5 * time.Second):
        t.Fatal("timed out waiting for event")
    }
}
```

## CI Patterns

```yaml
# GitHub Actions: integration tests with services
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm run test:integration
        env:
          DATABASE_URL: postgres://postgres:test@localhost:5432/postgres
```

**Do** separate unit and integration test commands — `npm test` vs `npm run test:integration`.

**Do** use Docker service containers in CI for databases and message brokers.

**Don't** run integration tests against shared staging databases — use ephemeral instances.
