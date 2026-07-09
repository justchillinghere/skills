# Observability And Workers

Observability and workers are part of backend design, not afterthoughts. The service should explain what it is doing through logs and metrics, and it should stop cleanly when the process shuts down.

## Logging

Configure logging once during process startup with `logging.config.dictConfig`.

Default goals:

- human-readable local logs
- consistent timestamp, level, logger name, and message
- environment-driven log level
- no secrets in logs
- meaningful exception boundaries with `exc_info`

Log at boundaries:

- process startup and shutdown
- worker start/stop/cancel/failure
- external API failures
- unexpected application errors
- important business state transitions when they are operationally useful

Do not scatter `basicConfig` across modules.

Prefer f-strings or preformatted messages for application logging in this style. Keep secret values out of logs.

## Prometheus Metrics

Expose Prometheus metrics on port `9000` by default. Start the metrics server during lifespan startup.

HTTP middleware should record:

- request count
- request duration
- method
- templated route path
- status code

Use the route template, not the raw URL. Avoid high-cardinality labels such as raw URLs, user IDs, request IDs, wallet addresses, exception messages, or arbitrary resource names.

Metrics can live in `metrics/` so routers and middleware reuse the same definitions.

## Worker Model

Most backend services eventually need workers: periodic sync, billing, cleanup, queue consumers, outbox processing, polling, reconciliation, cache refresh, or webhook backfill.

A worker has two parts:

- a loop/lifecycle wrapper that handles intervals, cancellation, logging, batching, and timeouts
- an application operation/use case that performs the business work

Keep the loop thin. The loop should not contain business rules.

## Worker Lifecycle

Create worker dependencies in `main.py` during startup, next to the API dependencies. Start tasks after shared resources are ready.

Worker rules:

- pass explicit dependency bundles
- use `asyncio.Event` for shutdown
- name tasks
- set intervals, timeouts, and batch sizes in settings
- catch/log expected per-item failures without killing the whole process when appropriate
- log unexpected task errors
- wait for tasks during shutdown, then cancel remaining tasks after a timeout
- close clients and DB engines after workers stop

Do not hide worker dependencies in module globals. Worker operations should call application use cases.
