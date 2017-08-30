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


RUN addgroup --system --gid 997 dockerhost
RUN addgroup jenkins dockerhost

# set timezone
ENV TZ="Europe/Zurich"
#RUN usermod -a -G docker jenkins
#RUN adduser jenkins staff
# drop back to the regular jenkins user - good practice
USER jenkins
RUN install-plugins.sh kubernetes docker-build-step
