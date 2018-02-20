..
    This file is part of Invenio.
    Copyright (C) 2017 RERO.

    Invenio is free software; you can redistribute it
    and/or modify it under the terms of the GNU General Public License as
    published by the Free Software Foundation; either version 2 of the
    License, or (at your option) any later version.

    Invenio is distributed in the hope that it will be
    useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Invenio; if not, write to the
    Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
    MA 02111-1307, USA.

    In applying this license, CERN does not
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
- a local directory in which the container will mount the ``virtualenv``; this local directory is named ``<local_dir.>`` in this documentation, and you have to change it accordingly to your file system organisation; **this** ``<local_dir.>`` **has to be created before the install processus is started**


Install the dev environment
---------------------------

This installation process needs to be done only once, except if you want to start anew.

**First**, copy and paste the following code in a ``docker-compose.yml`` file somewhere on your machine.

.. code:: console

    # -*- coding: utf-8 -*-
    #
    # This file is part of Invenio.
    # Copyright (C) 2015, 2016, 2017 CERN.
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
    # In applying this license, CERN does not
    # waive the privileges and immunities granted to it by virtue of its status
    # as an Intergovernmental Organization or submit itself to any jurisdiction.

    ## Usage: docker-compose up; docker-compose exec web ./populate.sh
    ## alias invenio='docker-compose exec web invenio'
    ## invenio --help
    ## tests: docker-compose exec web ./tests.sh
    ## debug: echo "FLASK_DEBUG=1" > .env; docker-compose up

    celery:
      restart: "always"
      image: rero/reroils-app:dev
      volumes:
        - changeit:/home/invenio/reroils:cached
      environment:
        - FLASK_DEBUG
        - INVENIO_SEARCH_ELASTIC_HOSTS=elasticsearch
        - INVENIO_SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://reroils:dbpass123@postgresql:5432/reroils
        - INVENIO_CELERY_BROKER_URL=amqp://guest:guest@rabbitmq:5672//
        - INVENIO_CELERY_RESULT_BACKEND=redis://redis:6379/1
        - INVENIO_CACHE_REDIS_URL = 'redis://redis:6379/1'
        - INVENIO_ACCOUNTS_SESSION_REDIS_URL='redis://redis:6379/0'
        - INVENIO_DB_VERSIONING=0
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
        - INVENIO_CACHE_REDIS_URL = 'redis://redis:6379/1'
        - INVENIO_ACCOUNTS_SESSION_REDIS_URL='redis://redis:6379/0'
        - INVENIO_DB_VERSIONING=0
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

**Once** this file is saved on your machine, change the two ``changeit`` occurrences by the path to your ``<local_dir.>``.

::

    l. 35   <local_dir.>:/home/invenio/reroils:cached
    l. 53   <local_dir.>:/home/invenio/reroils:cached

**Then**, run the following command from the directory where the ``docker-compose.yml`` file is saved:

.. code:: console

    docker-compose up

The first time [#]_, it should take some times, but then you'll have the sources in ``<local_dir.>/src/reroils-app``. You should be able to reach the reroils-app at http://localhost:5000.

**Finally**, populate the application with minimal data. Run the following command, still in the directory where the ``docker-compose.yml`` is saved:

.. code:: console

    docker-compose exec web ./populate.sh


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

**Keep in mind that this commands and aliases are available only in the** ``docker-compose.yml`` **directory!**


Debug Mode
----------

Sources changes won't be in effect unless you restart the application, or unless if ``FLASK_DEBUG`` is set to ``1``.

To activate the debug mode, you have to possibilities. You can edit the ``docker-compose.yml`` file and change the ``FLASK_DEBUG`` web environment variable (l. 55) to ``FLASK_DEBUG=1``.

Or, you can add this variable in a ``.env`` file aside your ``docker-compose.yml`` file:

.. code:: console

   echo "FLASK_DEBUG=1" > .env
   docker-compose up

To test it, you can modify the following file: ``<local_dir.>/src/reroils-app/reroils-app/templates/index.html``, save it and then reload http://localhost:5000.


Development workflow
--------------------

This suppose you have a development environment up and running.

The first time
..............

1. ``cd`` to the sources, ie ``<local_dir.>/src/reroils-app/reroils-app``
#. check that your master branch is up to date: ``git fetch``, or ``git reset --hard origin/master`` **Changes will be lost**
#. ``git checkout -b <your-dev-branch>`` to create a new branch for your developments
#. select a task your going to realize
#. assign the corresponding digital card to yourself
#. move the card into the *in progress* column
#. add the username of your pair in the card description, ie ``@<username>``
#. implement the task
#. once your done, run the test scripts
#. check the acceptance criterium and the definition of done for the current implementation
#. commit your changes with a well formated message
#. ``git checkout master`` to return into the master branch
#. ``git pull`` to fetch the remote modifications from the other members of the team
#. ``git rebase <your-dev-branch>`` to merge your developments into the master branch
#. run the tests scripts
#. ``git push`` to push your modifications into the remote master branch
#. move the related task in the *ready to test* column and announce the new state of this task in the next daily meeting
#. ask another developer to test this feature
#. once everything is ok, this developer will mark the card as *done*
#. once all task are done, check that the user story reach the acceptance criterium and the *how to demo*
#. the user story is to be marked as *ready for test*
#. the PO test the user story, notify the team that it's ready to deploy and mark it as *done* once it's deployed

When you resume developing
..........................

1. ``cd`` to the sources, ie ``<local_dir.>/src/reroils-app/reroils-app``
#. check your in the master branch
#. check that your master branch is up to date: ``git fetch``, or ``git reset --hard origin/master`` **Changes will be lost**
#. ``git checkout <your-dev-branch>`` to get into your dev branch
#. ``git rebase master`` to update you dev branch
#. continue since the point 5 from the above list

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
