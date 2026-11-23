# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

# Only analysis-icu: the bundled plugins are removed, then copied onto a fresh base to shrink the image.
FROM opensearchproject/opensearch:3.10.0 AS build
# A plugin that others depend on is removed on a later pass; the build fails if any is left.
RUN for _ in 1 2 3; do \
        for plugin in $(bin/opensearch-plugin list); do bin/opensearch-plugin remove "${plugin}" || true; done; \
    done \
    && [ -z "$(bin/opensearch-plugin list)" ] \
    && rm -r modules/ingest-geoip \
    && bin/opensearch-plugin install --batch analysis-icu

FROM amazonlinux:2023
RUN dnf install -y shadow-utils which && dnf clean all \
    && groupadd -g 1000 opensearch && adduser -u 1000 -g 1000 -d /usr/share/opensearch opensearch
COPY --from=build --chown=1000:1000 /usr/share/opensearch /usr/share/opensearch
WORKDIR /usr/share/opensearch
ENV JAVA_HOME=/usr/share/opensearch/jdk \
    PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/share/opensearch/jdk/bin:/usr/share/opensearch/bin
USER 1000
EXPOSE 9200 9300
ENTRYPOINT ["./opensearch-docker-entrypoint.sh"]
CMD ["opensearch"]
