..
    RERO ILS
    Copyright (C) 2019 RERO

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

RERO-ILS Installation
=====================

Services
--------

This environment makes use of different services. In most of the cases, RERO is an organisation and a ``reroadmin`` user exists. As long as users can be defined as administrator, the account ``reroadmin`` won't be used, except if needed.

The services are:

- GitHub_
- Travis_
- Docker_
- npm_
- Gitter_
- Transifex_
- PyPI [TODO]

Requirements
------------

- ``git``
- ``docker``, ``docker-compose``
- ``python``, ``pip``, ``pyenv``
- ``pipenv``

Installation
------------

First you need to install
`pipenv <https://docs.pipenv.org/install/#installing-pipenv>`_, it will handle
the virtual environment creation for the project in order to sandbox our Python
environment, as well as manage the dependency installation, among other things.

Create your working directory and ``cd`` into it. Clone inside this directory the project:

.. code-block:: console

    $ git clone https://github.com/rero/rero-ils.git

Next, ``cd`` into the project directory and bootstrap the instance (this will install
all Python dependencies and build all static assets):

.. code-block:: console

    $ cd rero-ils
    $ ./scripts/bootstrap

Start all dependent services using docker-compose (this will start PostgreSQL,
Elasticsearch 6, RabbitMQ and Redis):

.. code-block:: console

    $ docker-compose up -d


Make sure you have `enough virtual memory
<https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-cli-run-prod-mode>`_
for Elasticsearch in Docker:

.. code-block:: shell

    # Linux
    $ sysctl -w vm.max_map_count=262144

    # macOS
    $ screen ~/Library/Containers/com.docker.docker/Data/com.docker.driver.amd64-linux/tty
    <enter>
    linut00001:~# sysctl -w vm.max_map_count=262144


Next, create database tables, search indexes and message queues:

.. code-block:: console

    $ ./scripts/setup

Running
-------
Start the webserver and the celery worker:

.. code-block:: console

    $ ./scripts/server

Start a Python shell:

.. code-block:: console

    $ ./scripts/console

Upgrading
---------
In order to upgrade an existing instance simply run:

.. code-block:: console

    $ ./scripts/update

Testing
-------
Run the test suite via the provided script:

.. code-block:: console

    $ ./run-tests.sh

By default, end-to-end tests are skipped. You can include the E2E tests like
this:

.. code-block:: console

    $ env E2E=yes ./run-tests.sh

For more information about end-to-end testing see `pytest-invenio
<https://pytest-invenio.readthedocs.io/en/latest/usage.html#running-e2e-tests>`_.

Documentation
-------------
You can build the documentation with:

.. code-block:: console

    $ pipenv run build_sphinx

Production environment
----------------------
You can use simulate a full production environment using the
``docker-compose.full.yml``. You can start it like this:

.. code-block:: console

    $ docker build --rm -t rero/rero-ils-base:latest -f Dockerfile.base .
    $ docker-compose -f docker-compose.full.yml up -d

In addition to the normal ``docker-compose.yml``, this one will start:

- HAProxy (load balancer)
- Nginx (web frontend)
- UWSGI (application container)
- Celery (background task worker)
- Celery (background task beat)
- Flower (Celery monitoring)



.. References:
.. _GitHub: https://github.com/rero/rero-ils
.. _Travis: https://travis-ci.org/rero/rero-ils
.. _Docker: https://hub.docker.com/r/rero/rero-ils/
.. _npm: https://www.npmjs.com/org/rero
.. _Gitter: https://gitter.im/rero/interne
.. _Transifex: https://www.transifex.com/rero/reroils
