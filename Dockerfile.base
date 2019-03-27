# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

FROM python:3.6-slim-stretch

# require debian packages
RUN apt-get update -y && apt-get upgrade -y
RUN apt-get install --no-install-recommends -y git vim-tiny curl gcc gnupg libc6-dev && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade setuptools wheel pip pipenv

# # uwsgi uwsgitop uwsgi-tools

# Install Node
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN apt-get install --no-install-recommends -y nodejs && rm -rf /var/lib/apt/lists/*
RUN npm install --silent node-sass@4.9.0 clean-css@3.4.19 uglify-js@2.7.3 requirejs@2.2.0 @angular/cli@7.0.4

# RUN npm update

# RUN python -m site
# RUN python -m site --user-site

# Install Invenio
ENV WORKING_DIR=/invenio
ENV INVENIO_INSTANCE_PATH=${WORKING_DIR}/var/instance
RUN mkdir -p ${INVENIO_INSTANCE_PATH}

# copy everything inside /src
RUN mkdir -p ${WORKING_DIR}/src
COPY ./ ${WORKING_DIR}/src
WORKDIR ${WORKING_DIR}/src

# copy uwsgi config files
COPY ./docker/uwsgi/ ${INVENIO_INSTANCE_PATH}

# create user
RUN useradd invenio --uid 1000  --home ${WORKING_DIR} && \
    chown -R invenio:invenio ${WORKING_DIR} && \
    chmod -R go+w ${WORKING_DIR}

USER 1000
