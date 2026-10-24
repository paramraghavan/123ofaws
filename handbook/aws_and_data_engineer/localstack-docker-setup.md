# LocalStack And Docker Setup For Handbook Labs

Use this setup for the local AWS examples throughout this handbook. The default workflow uses `lstk` to manage the
Docker container and `lstk aws` for local AWS CLI calls. Plain `aws` commands elsewhere in the handbook target real AWS
unless an endpoint/profile is explicitly configured.

## Prerequisites And Authentication

Complete [Mac setup](setup.md) for Docker Desktop, CLI installation, login, and the S3 smoke test. Use
[the Jupyter guide](jupyter-lan-setup.md) for remote browser access. Keep LocalStack host-local; the browser only needs
to reach Jupyter or SSH. Do not publish the Docker engine API for notebook access.

`lstk login` authenticates the emulator license; `test` credentials identify simulated AWS API calls. Current emulator
service coverage depends on your license. `lstk aws` configures only its child AWS CLI process, not unrelated Python or
Spark processes. See [CLI proxy behavior](https://docs.localstack.cloud/aws/developer-tools/running-localstack/lstk/cloud-and-iac-commands/).

For host Python, source the `localstack.env` file created in [setup Step 5](setup.md#step-5-save-the-local-python-environment)
before starting Jupyter. The environment file applies to host Python; Compose token configuration is covered below.

## Endpoint Selection

| Client location | Endpoint |
|---|---|
| Mac-hosted Python/Jupyter/Spark, even with a remote browser | `http://localhost:4566` |
| Another container on the same Compose network | `http://localstack:4566` |
| Container accessing a host-published Docker Desktop port | `http://host.docker.internal:4566`, with a reachable binding |

Inside a container, `localhost` means that container. For deployed Lambda use supported runtime endpoint injection
rather than hardcoding the Mac's loopback address. S3 clients may need path-style access. Spark uses Hadoop S3A settings
and compatible jars separately from Boto3; see the
[Mac Spark guide](../../../sparksql-awsglue/help/quick101-spark/spark_quickstart/setup-mac-local-spark.md).

## Optional Project Configuration With lstk

From a lab project folder, create `.lstk/config.toml`:

```toml
[[containers]]
type = "aws"
tag = "latest"
port = "4566"
env = ["lab"]

[env.lab]
DEBUG = "0"
```

`latest` follows new releases. For a repeatable team lab, replace it with a tested image tag. Keep running `lstk` from
that project directory so it uses the same configuration. To change the host port, edit `port`, restart the emulator,
update the profile with `lstk setup aws --force`, and update Python/Spark endpoints too.

To retain supported service state, use `lstk start --type aws --persist` if your license supports persistence. A mounted
data directory alone does not enable service-state persistence. See
[lstk configuration](https://docs.localstack.cloud/aws/developer-tools/running-localstack/lstk/configuration/) and
[persistence coverage](https://docs.localstack.cloud/aws/developer-tools/snapshots/persistence/).

## Optional Docker Compose Workflow

Choose Compose when a project needs a shared container configuration. Stop the `lstk`-managed instance first with
`lstk stop`; do not start both on port 4566. With Compose, use Compose to start/stop the container and explicitly target
it with `lstk --endpoint-url http://localhost:4566 aws ...`.

Create `compose.yaml` in the project folder:

```yaml
services:
  localstack:
    image: localstack/localstack-pro:${LOCALSTACK_IMAGE_TAG:-latest}
    ports:
      - "127.0.0.1:4566:4566"
      - "127.0.0.1:4510-4559:4510-4559"
    environment:
      LOCALSTACK_AUTH_TOKEN: ${LOCALSTACK_AUTH_TOKEN:?Set LOCALSTACK_AUTH_TOKEN before starting}
      DEBUG: "0"
      PERSISTENCE: ${LOCALSTACK_PERSISTENCE:-0}
    volumes:
      - localstack-data:/var/lib/localstack
      # Required for Lambda/container-backed services; omit for S3-only labs.
      - /var/run/docker.sock:/var/run/docker.sock
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:4566/_localstack/health"]
      interval: 5s
      timeout: 5s
      retries: 30
      start_period: 20s

volumes:
  localstack-data:
```

Supply `LOCALSTACK_AUTH_TOKEN` from your LocalStack account through your shell/secret manager or an untracked `.env`
file. Browser login for `lstk` does not automatically populate Compose's environment. Never commit the token. Add
`.env`, `.venv/`, and `venv/` to your project's `.gitignore`.

```bash
# Token must already be provided. This validates configuration without starting containers.
docker compose config --quiet
docker compose up -d --wait
lstk --endpoint-url http://localhost:4566 aws s3api list-buckets
docker compose logs --tail 100 localstack
docker compose down
```

Compose reads `.env` for interpolation, not host Python configuration. Source `localstack.env` separately for Python.
The example defaults to no service-state persistence; set `LOCALSTACK_PERSISTENCE=1` only with a supporting license. `docker compose down` retains the named volume; `docker compose down -v` deletes it.
The Docker socket lets LocalStack launch containers and grants powerful access to the Docker engine.

## Daily Workflow And Troubleshooting

| Need | lstk-managed instance | Compose-managed instance |
|---|---|---|
| Start | `lstk start --type aws` | `docker compose up -d --wait` |
| Inspect | `lstk status` | `docker compose ps` |
| Logs | `lstk logs --tail 100` | `docker compose logs --tail 100 localstack` |
| Local S3 | `lstk aws s3 ls` | `lstk --endpoint-url http://localhost:4566 aws s3 ls` |
| Stop | `lstk stop` | `docker compose down` |

If port 4566 is busy, inspect `docker ps` and, on macOS, `lsof -nP -iTCP:4566 -sTCP:LISTEN`. Stop only the instance you
intend to replace; do not kill an unknown process. For license failures, check `lstk login` or the Compose auth token.
For Lambda failures, check Docker socket access, runtime image architecture, service entitlement, and logs. Use native
Apple Silicon images when supported; choose Lambda `arm64` or `x86_64` to match your intended runtime and dependencies.
LocalStack is useful for development; validate IAM, networking, quotas, and production behavior in an AWS sandbox.
