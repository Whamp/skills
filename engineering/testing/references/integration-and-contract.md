# Integration and contract testing

Use integration evidence when the risk sits at a boundary: serialization, schema, database behavior, process lifecycle, network transport, message delivery, filesystem semantics, or a consumer-provider agreement.

## Choose the boundary

Name what the test crosses and what a narrower test cannot detect. Distinguish these surfaces instead of calling each one a "real server":

| Surface | What it can detect |
| --- | --- |
| In-process handler or application transport | Routing, middleware, serialization, validation, and application lifecycle included by that transport |
| Bound test server | Socket, port, TLS, proxy, and server-start or shutdown behavior included by the setup |
| Real database engine | SQL dialect, constraints, transaction behavior, migrations, and driver integration |
| Test double for an external service | The client's behavior for the responses and failures encoded by the double |
| Real broker | Acknowledgement, redelivery, ordering, reconnection, and broker configuration included by the scenario |
| Contract test | The request, response, or message fields a consumer actually depends on |

Use the narrowest surface that includes the mismatch at risk. State what every fake omits and what every real dependency costs.

## HTTP applications

Exercise the application's real routing and serialization path. Choose in-process or bound-server execution according to whether transport behavior matters.

- Python ASGI tests use `httpx.ASGITransport(app=app)` with `AsyncClient(transport=..., base_url=...)`. HTTPX does not trigger lifespan events; use the application's established lifespan test helper when startup or shutdown matters.
- Go handler tests use `httptest.NewRequest` or `NewRequestWithContext` with `httptest.NewRecorder`; use `httptest.NewServer` or `NewTLSServer` when a real client transport is part of the risk.
- Node tests may call the framework's maintained in-process helper or own an `http.Server` lifecycle explicitly. A bound server test must close the server and any open connections it created.

Assert response status, headers, and body fields that form the public contract. Include malformed input, authorization, error mapping, and content negotiation only when those behaviors are in scope.

## Databases and migrations

Use the production database engine when engine behavior is part of the risk. Create a schema and data lifecycle that is isolated at the suite, worker, database, schema, or transaction level according to the repository's cost budget.

A rollback fixture isolates only work contained by its transaction. Sequences and external effects may survive rollback; some engines and DDL operations implicitly commit or cannot be reversed. Never describe transaction rollback as a universally clean database reset.

For a migration:

1. start from every supported deployed schema, not only an empty database
2. load representative rows that exercise nullability, uniqueness, size, and legacy values relevant to the change
3. apply the forward migration
4. run the old/new application compatibility checks required by the rollout plan
5. verify schema and behavior through supported queries
6. test a down migration only when the migration system supplies one and the operations support the claimed reversal

Re-applying after a down migration tests one sequence; it does not by itself prove idempotence. Destructive or expand-contract rollout guidance must come from the project's actual deployment policy.

## Consumer-driven and schema contracts

A Pact consumer test should invoke the real consumer client against Pact's mock provider and describe only the request and minimal response fields the consumer uses. Keep interactions independent; express setup through provider states. Provider verification then replays each interaction against the provider. Use the Pact Broker deployment matrix and `can-i-deploy` when the project already operates that workflow.

Contract tests do not replace provider functional tests. Pact message contracts validate message shape, not Kafka, RabbitMQ, or another broker's delivery behavior.

Use Schemathesis when an OpenAPI or GraphQL schema should generate requests and stateful workflows against an implementation. Treat failures as reproducible contract examples; do not equate schema conformance with business correctness.

## Messages and eventual completion

Test domain message handlers without a broker when the claim concerns payload interpretation alone. Use the real broker when acknowledgement, publisher confirms, redelivery, ordering, consumer groups, reconnection, or broker configuration is the risk.

At-least-once delivery can produce duplicates. Test the application's idempotency or deduplication contract where delivery semantics require it. For RabbitMQ, acknowledge only after the required operation completes; test retransmission and reconnection around publisher confirms and consumer acknowledgements.

Wait on an observable completion signal with a deadline: a received message, committed row, emitted event, or stable public query. Fixed sleeps add delay without proving readiness. Include enough timeout diagnostics to distinguish no publication, no consumption, failed processing, and slow infrastructure.

## Lifecycle and CI

Prefer ephemeral dependencies or isolated namespaces over a shared mutable staging service. Match container scope to isolation: one per test is strongest and most expensive; one per worker or suite needs explicit state reset. Readiness checks prove availability, not clean state.

Record image and service versions, own start and stop, and preserve dependency logs on failure. Run the boundary test alone and under intended parallelism before trusting it.

## Primary references

- [HTTPX transports](https://www.python-httpx.org/advanced/transports/)
- [Go `httptest`](https://pkg.go.dev/net/http/httptest)
- [Node HTTP](https://nodejs.org/api/http.html)
- [PostgreSQL transaction isolation](https://www.postgresql.org/docs/current/transaction-iso.html)
- [Pact: how Pact works](https://docs.pact.io/getting_started/how_pact_works)
- [Pact Broker: can-i-deploy](https://docs.pact.io/pact_broker/can_i_deploy)
- [Schemathesis](https://schemathesis.readthedocs.io/en/stable/)
- [RabbitMQ reliability guide](https://www.rabbitmq.com/docs/reliability)
- [Testcontainers lifecycle guidance](https://testcontainers.com/guides/testcontainers-container-lifecycle/)
