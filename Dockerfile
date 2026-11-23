# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

FROM python:3.14-slim-bookworm AS base

RUN apt-get update -y && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y vim-tiny curl procps imagemagick \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip uv

ENV WORKING_DIR=/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance
RUN useradd invenio --uid 1000 --home ${WORKING_DIR} \
    && mkdir -p ${INVENIO_INSTANCE_PATH} ${WORKING_DIR}/src \
    && chown -R invenio:invenio ${WORKING_DIR} \
    && chmod -R go+w ${WORKING_DIR}
WORKDIR ${WORKING_DIR}/src
USER 1000

# Without UV_NO_SYNC, `uv run` would install the dev group.
ENV INVENIO_COLLECT_STORAGE='flask_collect.storage.file' \
    LANG=C.UTF-8 \
    UV_NO_CACHE=1 \
    UV_NO_SYNC=1

# Node.js is only needed to build the web assets.
FROM base AS build
USER root
RUN apt-get update -y && apt-get install --no-install-recommends -y gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_24.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update -y && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*
USER 1000

COPY --chown=invenio:invenio pyproject.toml uv.lock ./
RUN uv sync --frozen --no-group dev --group prod --no-install-project

COPY --chown=invenio:invenio ./ ./
ARG UI_TGZ=""
RUN uv run --no-sync ./scripts/bootstrap --deploy ${UI_TGZ}

FROM base
COPY --from=build --chown=invenio:invenio ${WORKING_DIR}/src ${WORKING_DIR}/src
COPY --from=build --chown=invenio:invenio ${INVENIO_INSTANCE_PATH}/static ${INVENIO_INSTANCE_PATH}/static

ARG GIT_HASH
ENV INVENIO_RERO_ILS_GIT_HASH=${GIT_HASH:-''}
ARG GIT_UI_HASH
ENV INVENIO_RERO_ILS_UI_GIT_HASH=${GIT_UI_HASH:-''}
