FROM python:3.5-slim

LABEL maintainer="software@rero.ch"
LABEL description="Integrated Library System flavour of Invenio by RERO."

RUN apt-get update && apt-get install -y curl \
    && curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs gcc \
    && pip install -U setuptools pip && \
	pip install -U virtualenv


# Add Invenio sources to `code` and work there:
WORKDIR /reroils/reroils/src/reroils-app
COPY setup.py /reroils/reroils/src/reroils-app/
COPY MANIFEST.in /reroils/reroils/src/reroils-app/
COPY reroils_app /reroils/reroils/src/reroils-app/reroils_app


# # Run container as user `invenio` with UID `1000`, which should match
# # current host user in most situations:
RUN adduser --uid 1000 --disabled-password --gecos '' invenio && \
     chown -R invenio:invenio /reroils

USER invenio

SHELL ["/bin/bash", "-c"]
WORKDIR /reroils
RUN virtualenv reroils
RUN source reroils/bin/activate && \
    pip install reroils/src/reroils-app && \
    pip install gunicorn

RUN source reroils/bin/activate && \
	node --version &&\
	npm install -g --prefix ${VIRTUAL_ENV} npm &&\
	npm install -g --prefix ${VIRTUAL_ENV} node-sass clean-css clean-css-cli requirejs uglify-js &&\
	invenio npm && \
	cd reroils/var/instance/static && \
	npm i && \
	invenio collect -v && \
	invenio assets build

USER root
RUN rm -rf /var/lib/apt/lists/*

USER invenio
CMD ["/reroils/reroils/bin/gunicorn", "-w", "3", "-b", "0.0.0.0:5000", "invenio_app.wsgi"]
