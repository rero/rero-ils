# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

# The haproxy image ships no openssl, so the pair is built in a separate stage.
# It borrows the nginx image, which the stack already pulls for its own service,
# rather than adding one just for a certificate.
FROM nginx AS certs
RUN openssl req -x509 -newkey rsa:4096 -sha256 -days 825 -nodes \
      -keyout /key.pem -out /crt.pem \
      -subj "/CN=localhost" \
      -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" \
    && cat /crt.pem /key.pem > /cert.pem \
    && chmod 600 /cert.pem

FROM haproxy:1.8
RUN mkdir -p /usr/local/var/lib/haproxy/
COPY haproxy.cfg /usr/local/etc/haproxy/haproxy.cfg
COPY --from=certs /cert.pem /usr/local/etc/cert.pem
