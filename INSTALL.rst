..
    This file is part of REROILS.
    Copyright (C) 2017 RERO.

    REROILS is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    REROILS is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with REROILS; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, RERO does not
    waive the privileges and immunities granted to it by virtue of its status
    as an Intergovernmental Organization or submit itself to any jurisdiction.

============
Installation
============

Services
--------

This environment makes use of different services. In most of the cases, RERO is an organisation and a ``reroadmin`` user exists. As long as users can be defined as administrator, the account ``reroadmin`` won't be used, except if needed.

The services are:

- GitHub_
- Travis_
- Docker_
- npm_
- Gitter_
- Transiflex_
- PyPI [TODO]


Requirements
------------

- ``git``
- ``docker``
- ``docker-compose``
- a local directory in which the container will mount the ``virtualenv``; this local directory is named ``<local_dir.>`` in this documentation, and you have to change it accordingly to your file system organisation; **this** ``<local_dir.>`` **has to be created before the install process is started**


Install the dev environment
---------------------------

This installation process needs to be done only once, except if you want to start anew.


**First**, copy and paste the following code in a ``docker-compose.yml`` file somewhere on your machine.

.. code:: console

    # -*- coding: utf-8 -*-
    #
    # This file is part of Invenio.
    # Copyright (C) 2015, 2016, 2017 RERO.
    #
    # Invenio is free software; you can redistribute it
    # and/or modify it under the terms of the GNU General Public License as
    # published by the Free Software Foundation; either version 2 of the
    # License, or (at your option) any later version.
    #
    # Invenio is distributed in the hope that it will be
    # useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    # General Public License for more details.
    #
    # You should have received a copy of the GNU General Public License
    # along with Invenio; if not, write to the
    # Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    # MA 02111-1307, USA.
    #
    # In applying this license, RERO does not
    # waive the privileges and immunities granted to it by virtue of its status
    # as an Intergovernmental Organization or submit itself to any jurisdiction.

    ## Usage: docker-compose up; docker-compose exec web ./populate.sh
    ## alias invenio='docker-compose exec web invenio'
    ## invenio --help
    ## tests: docker-compose exec web ./tests.sh
    ## debug: echo "FLASK_DEBUG=1" > .env; docker-compose up
    ## WARNING: do not insert spaces around '='


    celery:
      restart: "always"
      image: rero/reroils-app:dev
      volumes:
        - changeit:/home/invenio/reroils:cached
      environment:
        - FLASK_DEBUG=1
        - INVENIO_SEARCH_ELASTIC_HOSTS=elasticsearch
        - INVENIO_SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://reroils:dbpass123@postgresql:5432/reroils
        - INVENIO_CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
        - INVENIO_CELERY_RESULT_BACKEND=redis://redis:6379/1
        - INVENIO_CACHE_REDIS_URL='redis://redis:6379/1'
        - INVENIO_ACCOUNTS_SESSION_REDIS_URL='redis://redis:6379/0'
        - INVENIO_DB_VERSIONING=0
        # To send email in dev mode e.g. user registration (uncomment and change value)
        # - INVENIO_MAIL_SUPPRESS_SEND=0
        # - INVENIO_MAIL_SERVER='changeit'
        # - INVENIO_SECURITY_EMAIL_SENDER='changeit'
      links:
        - postgresql
        - redis
        - elasticsearch
        - rabbitmq
      command: ['./celery.sh']

    web:
      restart: "always"
      image: rero/reroils-app:dev
      volumes:
        - changeit:/home/invenio/reroils:cached
      environment:
        - FLASK_DEBUG=1
        - INVENIO_SEARCH_ELASTIC_HOSTS=elasticsearch
        - INVENIO_SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://reroils:dbpass123@postgresql:5432/reroils
        - INVENIO_CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
        - INVENIO_CELERY_RESULT_BACKEND=redis://redis:6379/1
        - INVENIO_CACHE_REDIS_URL='redis://redis:6379/1'
        - INVENIO_ACCOUNTS_SESSION_REDIS_URL='redis://redis:6379/0'
        - INVENIO_DB_VERSIONING=0
        # To send email in dev mode e.g. user registration (uncomment and change value)
        # - INVENIO_MAIL_SUPPRESS_SEND=0
        # - INVENIO_MAIL_SERVER='changeit'
        # - INVENIO_SECURITY_EMAIL_SENDER='changeit'
      links:
        - postgresql
        - redis
        - elasticsearch
        - rabbitmq
      ports:
        - "5000:5010"
      command: ['./start.sh']

    postgresql:
      restart: "always"
      image: postgres
      environment:
        - POSTGRES_USER=reroils
        - POSTGRES_DB=reroils
        - POSTGRES_PASSWORD=dbpass123
      ports:
        - "25432:5432"

    redis:
      restart: "always"
      image: redis
      ports:
        - "26379:6379"

    elasticsearch:
      restart: "always"
      image: elasticsearch:2
      # dockerfile: Dockerfile_elastic
      ports:
        - "29200:9200"
        - "29300:9300"

    rabbitmq:
      restart: "always"
      image: rabbitmq:3-management
      ports:
        - "24369:4369"
        - "21567:15672"

**Once** this file is saved on your machine, change the *two* ``changeit`` occurrences by the path to your ``<local_dir.>``. These occurrences are in the celery and web configurations.

::

    changeit:/home/invenio/reroils:cached

To enable email sending in development mode, uncomment and change the value of the following lines, again in the celery and web configurations (two times, then):

::

    #- INVENIO_MAIL_SUPPRESS_SEND=0
    #- INVENIO_MAIL_SERVER='changeit'
    #- INVENIO_SECURITY_EMAIL_SENDER='changeit'

**Then**, run the following command from the directory where the ``docker-compose.yml`` file is saved:

.. code:: console

    docker-compose up

The first time [#]_, it should take some times, but then you'll have the sources in ``<local_dir.>/src/reroils-app``. You should be able to reach the reroils-app at http://localhost:5000.

**Finally**, populate the application with minimal data. Run the following command, still in the directory where the ``docker-compose.yml`` is saved:

.. code:: console

    docker-compose exec web ./populate.sh

This script will generate 10.000 bibliographic records, but create only items for 1.000 of them, due to performance reason. If you need more items, edit the ``reroils-app/development/docker/populate.sh`` script and change the line ``invenio fixtures createitems -c 1000`` into ``invenio fixtures createitems -c 10000``, or the number you want.


Update the development environment
----------------------------------

As new modules are developed, you may need to update the development environment. To do so, follow these steps:

Stop the running containers. `cd` to the directory where the `docker-compose.yml` file is, and run:

.. code:: console

   docker-compose down

Update your `git` local master branch:

.. code:: console

   git pull

Update the docker images from the RERO registry and start the containers. Don't forget to `cd` to the directory where the `docker-compose.yml` file is and run:

.. code:: console

   docker-compose pull
   docker-compose up

Force the `install.sh` script, and launch the `populate.sh` script:

.. code:: console

   docker-compose exec web ./install.sh -f
   docker-compose exec web ./populate.sh


Invenio commands
----------------

Once the container is started you should be able to run invenio commands like this:

.. code:: console

   docker-compose exec web invenio --help

You can write an alias:

.. code:: console

  alias reroils=`docker-compose exec web invenio`

Then you can run:

.. code:: console

   reroils --help
   reroils db create

**Keep in mind that these commands and aliases are available only in the** ``docker-compose.yml`` **directory!**


Debug Mode
----------

Sources changes won't be in effect unless you restart the application, or unless if ``FLASK_DEBUG`` is set to ``1``.

To activate the debug mode, you have two possibilities. You can edit the ``docker-compose.yml`` file and change the ``FLASK_DEBUG`` web environment variable (l. 55) to ``FLASK_DEBUG=1``.

Or, you can add this variable in a ``.env`` file aside your ``docker-compose.yml`` file:

.. code:: console

   echo "FLASK_DEBUG=1" > .env
   docker-compose up

To test it, you can modify the following file: ``<local_dir.>/src/reroils-app/reroils-app/templates/index.html``, save it and then reload http://localhost:5000.


Development workflow
--------------------

This supposes you have a development environment up and running.

The first time
..............

1. Fork the RERO project on your own GitHub account
#. ``cd`` to the sources, ie ``<local_dir.>/src/<module>/<module>``
#. add the remote URL of your fork (``git remote add <choose-a-name> <your-fork-url>``)
#. ``git checkout -b <your-dev-branch> <the-name-of-your-repository>/<your-dev-branch>`` to create a new branch
#. develop on the new branch you just created
#. once you're done, run the test scripts

.. code:: console

    docker-compose run web bash
    cd /home/invenio/reroils/src/<module>
    ./run-tests.sh


#. if it complains about the manifest, it is because new files had been added, but they aren't registered into the MANIFEST.in file, so let's do so (from inside the container): ``check-manifest -u``
#. commit your changes with a well formated message (see the Commit Messages section below)
#. ``git push <your-repository>`` to push your modifications into your branch
#. Make a Pull Request on GitHub

When you resume developing
..........................

1. ``cd`` to the sources, ie ``<local_dir.>/src/<module>/<module>``
#. check you're in the master branch
#. check that your master branch is up to date: ``git fetch origin``, or ``git reset --hard origin/master`` **Changes will be lost**
#. ``git checkout <your-dev-branch>`` to get into your dev branch
#. ``git rebase master`` to update you dev branch
#. continue from the point 5 from the above list

Commit Messages
................

As defined by the `invenio documentation`_ but instead of `component` we can use `type`.

Type must be one of the following
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-   **feat**: A new feature
-   **fix**: A bug fix
-   **docs**: Only documentation changes
-   **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing
    semi-colons, etc)
-   **refactor**: A code change that neither fixes a bug nor adds a feature
-   **perf**: A code change that improves performance
-   **test**: Adding missing tests
-   **core**: Changes to the build process or auxiliary tools and libraries such as documentation
    generation


.. References:
.. _GitHub: https://github.com/rero/reroils-app
.. _Travis: https://travis-ci.org/rero/reroils-app
.. _Docker: https://hub.docker.com/r/rero/reroils-app/
.. _npm: https://www.npmjs.com/org/rero
.. _Gitter: https://gitter.im/rero/interne
.. _Transiflex: https://www.transifex.com/rero/reroils
.. _gitlab.rero.ch: https://gitlab.rero.ch
.. _invenio documentation: http://invenio.readthedocs.io/en/latest/community/contribution-guide.html?highlight=commit%20message
.. [#] If you want to update your installation instead of installing it for the first time, check the *Updating your installation* section


Invenio Installation
====================

First you need to install
`pipenv <https://docs.pipenv.org/install/#installing-pipenv>`_, it will handle
the virtual environment creation for the project in order to sandbox our Python
environment, as well as manage the dependency installation, among other things.

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
<https://pytest-invenio.readthedocs.io/en/latest/usage.html#running-e2e-tests>`_

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

    $ docker-compose -f docker-compose.full.yml up -d

In addition to the normal ``docker-compose.yml``, this one will start:

- HAProxy (load balancer)
- Nginx (web frontend)
- UWSGI (application container)
- Celery (background task worker)
- Flower (Celery monitoring)
