# -*- coding: utf-8 -*-

"""reroils-app base Invenio configuration."""

from __future__ import absolute_import, print_function

"""
Cli commands can be added here, for example:

.. code:: python

    import click

    @click.group()
    def avangers():
        \"\"\"Avengers commands.\"\"\"

    @avengers.command('init')
    def init():
        \"\"\"Initialize the Avengers team.\"\"\"
        click.secho('Calling the team', fg='green')

On the ```setup.py``` the ```entry_points``` should be updated

.. code:: python
    entry_points={
        'flask.commands': [
            'avengers = '
            'reroils-app.cli:avengers'
        ],
    }

Now on the console

.. code:: console

    $ invenio avangers --help
    $ invenio avangers init
"""
