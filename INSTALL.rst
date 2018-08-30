..
    Copyright (C) 2018 RERO.

    reroils-app is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

Installation
============

First, create a `virtualenv <https://virtualenv.pypa.io/en/stable/installation/>`_
using `virtualenvwrapper <https://virtualenvwrapper.readthedocs.io/en/latest/install.html>`_
in order to sandbox our Python environment for development:

.. code-block:: console

    $ mkvirtualenv my-site

Start all dependent services using docker-compose (this will start PostgreSQL,
Elasticsearch 6, RabbitMQ and Redis):

.. code-block:: console

    $ docker-compose up -d

.. note::

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


Next, bootstrap the instance (this will install all Python dependencies and
build all static assets):

.. code-block:: console

    $ ./scripts/bootstrap

Next, create database tables, search indexes and message queues:

.. code-block:: console

    $ ./scripts/setup

Running
-------
Start the webserver:

.. code-block:: console

    $ ./scripts/server

Start the a background worker:

.. code-block:: console

    $ celery worker -A invenio_app.celery -l INFO

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
<https://pytest-invenio.readthedocs.io/en/latest/usage.html#running-e2e-tests>`_

Documentation
-------------
You can build the documentation with:

.. code-block:: console

    $ python setup.py build_sphinx

Production environment
----------------------
You can use simulate a full production environment using the
``docker-compose.full.yml``. You can start it like this:

.. code-block:: console

    $ docker-compose -f docker-compose.full.yml up -d

In addition to the normal ``docker-compose.yml``, this one will start:

- HAProxy (load balancer)
- Nginx (web frontend)
- UWSGI (application container)
- Celery (background task worker)
- Flower (Celery monitoring)
