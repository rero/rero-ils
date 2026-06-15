# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

ARG VERSION=latest
FROM rero/rero-ils-base:${VERSION}

USER 0

COPY ./ ${WORKING_DIR}/src
WORKDIR ${WORKING_DIR}/src
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}

RUN chown -R invenio:invenio ${WORKING_DIR}

USER 1000

ARG GIT_HASH
ENV INVENIO_RERO_ILS_GIT_HASH=${GIT_HASH:-''}
ARG GIT_UI_HASH
ENV INVENIO_RERO_ILS_UI_GIT_HASH=${GIT_UI_HASH:-''}
ARG UI_TGZ=""

ENV INVENIO_COLLECT_STORAGE='flask_collect.storage.file'

RUN uv run --no-sync ./scripts/bootstrap --deploy ${UI_TGZ}
