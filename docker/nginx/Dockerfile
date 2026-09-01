# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

FROM nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/* /etc/nginx/conf.d/

# Self-signed pair for this example stack, generated at build time rather than
# versioned. The nginx image ships openssl, so no extra stage is needed.
RUN openssl req -x509 -newkey rsa:4096 -sha256 -days 825 -nodes \
      -keyout /etc/ssl/private/test.key -out /etc/ssl/certs/test.crt \
      -subj "/CN=localhost" \
      -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
    && chmod 600 /etc/ssl/private/test.key
