<!--
SPDX-FileCopyrightText: Fondation RERO+
SPDX-License-Identifier: AGPL-3.0-or-later
-->

# RERO-ILS Installation

## Requirements

- `git`
- `docker`, `docker-compose`
- `python`, `pip`, `pyenv`
- `uv`

## Installation

First, create your working directory and `cd` into it. Clone the project into this directory:

```console
git clone https://github.com/rero/rero-ils.git
```

You need to install `uv`, it will handle the virtual environment creation for the project
in order to sandbox our Python environment, as well as manage the dependency installation,
among other things.

```console
pyenv install 3.14
cd rero-ils
pyenv local 3.14
curl -LsSf https://astral.sh/uv/install.sh | sh
```

See the [uv installation documentation](https://docs.astral.sh/uv/getting-started/installation) for more detail.

Next, `cd` into the project directory and bootstrap the instance (this will install
all Python dependencies and build all static assets):

```console
cd rero-ils
uv run ./scripts/bootstrap
```

### TLS certificates

The development server is served over HTTPS. The bootstrap generates its
certificate and private key in the git-ignored `.certs/` directory. An existing
pair is kept; `--force-certs` replaces it.

If [mkcert](https://github.com/FiloSottile/mkcert) is installed, the pair is
signed by a local certificate authority and browsers accept it without warning.
Run `mkcert -install` once to trust that authority. Otherwise the script falls
back to a self-signed certificate from `openssl`, which works but makes browsers
warn about the unknown issuer.

To regenerate the pair on its own:

```console
uv run ./scripts/gen-certs --force
```

Start all dependent services using docker-compose (this will start PostgreSQL,
OpenSearch 3, RabbitMQ and Redis):

```console
docker-compose up -d
```

For local work, `docker-compose-extra.yml` adds Flower, OpenSearch Dashboards,
Redis Insight and Mailpit:

```console
docker compose -f docker-compose.yml -f docker-compose-extra.yml up -d
```

The host ports default to the standard ones. To run several projects side
by side, copy `.env.example` to `.env` and set other ports there: the
application reads its endpoints from the same file. The tests ignore it.

Make sure you have [enough virtual memory](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/docker/#important-host-settings)
for OpenSearch in Docker:

```shell
# Linux
sysctl -w vm.max_map_count=262144

# macOS
screen ~/Library/Containers/com.docker.docker/Data/com.docker.driver.amd64-linux/tty
# press <enter>
linut00001:~# sysctl -w vm.max_map_count=262144
```

Next, create database tables, search indexes and message queues:

```console
uv run poe setup
```

## Running

Start the webserver and the celery worker:

```console
uv run poe server
```

Start a Python shell:

```console
uv run poe console
```

## Upgrading

In order to upgrade an existing instance simply run:

```console
uv run poe update
```

## Testing

Run the test suite via the provided script:

```console
uv run poe run_tests
```

By default, end-to-end tests are skipped.
