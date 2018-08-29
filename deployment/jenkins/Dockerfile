# -*- coding: utf-8 -*-
#
# This file is part of REROILS.
# Copyright (C) 2017 RERO.
#
# REROILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# REROILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with REROILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

FROM jenkins/jenkins:lts
# https://github.com/jenkinsci/docker/blob/master/README.md

# if we want to install via apt
USER root

#RUN apt-get update && apt-get install -y kubectl
# kubectl
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl \
    && chmod +x ./kubectl \
    && mv ./kubectl /usr/local/bin/kubectl

# docker
RUN   apt-get update \
  && apt-get install -y \
     apt-transport-https \
     ca-certificates \
     curl \
     gnupg2 \
     software-properties-common \
  && curl -fsSL https://download.docker.com/linux/debian/gpg | apt-key add - \
  && add-apt-repository \
     "deb [arch=amd64] https://download.docker.com/linux/debian \
      $(lsb_release -cs) \
      stable" \
  && apt-get update && apt-get install -y docker-ce


RUN addgroup --system --gid 996 dockerhost
RUN addgroup jenkins dockerhost

# set timezone
ENV TZ="Europe/Zurich"
#RUN usermod -a -G docker jenkins
#RUN adduser jenkins staff
# drop back to the regular jenkins user - good practice
USER jenkins
RUN install-plugins.sh kubernetes docker-build-step
