# PROBLEM STATEMENT

```mermaid
┌─────────┐      ┌─────────────┐      ┌────────────┐
│   SQS   │ ───► │   Lambda    │ ───► │  Postgres  │
│  Queue  │      │  (Python)   │      │   Table    │
└─────────┘      └─────────────┘      └────────────┘
```

- write a lambda that will read sqs from time to time and parse the json message and write to postgresdb



