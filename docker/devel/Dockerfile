FROM python:3.5-slim

LABEL maintainer="software@rero.ch"
LABEL description="Integrated Library System flavour of Invenio by RERO. Devel version."

RUN apt-get update && apt-get install -y curl \
    && curl -sL https://deb.nodesource.com/setup_6.x | bash - \
    && apt-get install -y nodejs gcc git \
    && pip install -U setuptools pip && \
	pip install -U virtualenv


# # Run container as user `invenio` with UID `1000`, which should match
# # current host user in most situations:
RUN adduser --uid 1000 --disabled-password --gecos '' invenio

USER invenio

# make invenio command available by default
RUN echo "if [ -f /home/invenio/reroils/bin/activate ]; then \n\
    source /home/invenio/reroils/bin/activate \n\
fi" >> ~/.bashrc


WORKDIR /home/invenio

# Debug mode by default
ENV FLASK_DEBUG=1
ENV PATH=$PATH:/home/invenio/reroils/bin

# put install script
ADD install.sh /home/invenio
ADD start.sh /home/invenio
ADD populate.sh /home/invenio
ADD celery.sh /home/invenio
# default command
CMD /home/invenio/start.sh
