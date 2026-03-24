<!--
  RERO ILS
  Copyright (C) 2019-2026 RERO+

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU Affero General Public License as published by
  the Free Software Foundation, version 3 of the License.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public License
  along with this program. If not, see <http://www.gnu.org/licenses/>.
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

Start all dependent services using docker-compose (this will start PostgreSQL,
Elasticsearch 6, RabbitMQ and Redis):

```console
docker-compose up -d
```

Make sure you have [enough virtual memory](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode)
for Elasticsearch in Docker:

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

## Production environment

You can simulate a full production environment using `docker-compose.full.yml`:

```console
docker build --rm -t rero/rero-ils-base:latest -f Dockerfile.base .
docker-compose -f docker-compose.full.yml up -d
```

In addition to the normal `docker-compose.yml`, this one will start:

- HAProxy (load balancer)
- Nginx (web frontend)
- UWSGI (application container)
- Celery (background task worker)
- Celery (background task beat)
- Flower (Celery monitoring)
