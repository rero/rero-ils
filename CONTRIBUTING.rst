..
    RERO ILS
    Copyright (C) 2019-2022 RERO+

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, version 3 of the License.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.


Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

Types of Contributions
----------------------

Security reports
~~~~~~~~~~~~~~~~

In case you identified a security issue on the project, please report it to the
e-mail address given in the `security policy`_.

Bug reports
~~~~~~~~~~~

Report bugs at https://github.com/rero/rero-ils/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Bug fixes
~~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "feature"
or "enhancement" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

rero-ils could always use more documentation, whether as part of the
official rero-ils docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at
https://github.com/rero/rero-ils/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

Ready to contribute? See the `installation procedure`_ to setup a local
development environment.



Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests and should not decrease test coverage.
2. Your code is as clear as possible and sufficiently documented (comments, 
   docstrings, ...).
3. All tests on GitHub Actions should pass before merging.

Commit message style
~~~~~~~~~~~~~~~~~~~~

Your commit message should follow Invenio's `style guide`_. Commit message is first and foremost about the content. You are communicating
with fellow developers, so be clear and brief.

(Inspired by `How to Write a Git Commit Message
<https://chris.beams.io/posts/git-commit/>`_)

1. `Separate subject from body with a blank line.
   <https://chris.beams.io/posts/git-commit/#separate>`_
2. `Limit the subject line to 50 characters.
   <https://chris.beams.io/posts/git-commit/#limit-50>`_
3. Indicate the component followed by a short description
4. `Do not end the subject line with a period.
   <https://chris.beams.io/posts/git-commit/#end>`_
5. `Use the imperative mood in the subject line.
   <https://chris.beams.io/posts/git-commit/#imperative>`_
6. `Wrap the body at 72 characters.
   <https://chris.beams.io/posts/git-commit/#wrap-72>`_
7. `Use the body to explain what and why vs. how, using bullet points. <https://chris.beams.io/posts/git-commit/#why-not-how>`_

For example::

   component: summarize changes in 50 char or less

    * More detailed explanatory text, if necessary. Formatted using
      bullet points, preferably `*`. Wrapped to 72 characters.

    * Explain the problem that this commit is solving. Focus on why you
      are making this change as opposed to how (the code explains that).
      Are there side effects or other unintuitive consequences of this
      change? Here's the place to explain them.

    * Data Migration Instructions: if your PR makes changes to the data model
      or needs an action when updating an existing instance, include
      migration instructions (e.g. needs item reindexing, needs update mapping).
      It is even better if you can also include an Alembic script directly in
      your PR.

    * Use words like "Adds", "Fixes" or "Breaks" in the listed bullets to help
      others understand what you did.

    * If your commit closes or addresses an issue in the same project, you can
      mention it in any of the bullets after the dot (closes #XXX). If it
      addresses an issue from another project, mention the full issue URL
      (Closes https://github.com/rero/rero-ils/issues/XXX).

   Co-authored-by: John Doe <john.doe@example.com>

**Git signature:** The only signature we use is ``Co-authored-by`` (see above)
to provide credit to co-authors. Previously we required a ``Signed-off-by``
signature, however this is no longer required.

.. References:
.. _installation procedure: INSTALL.rst
.. _security policy: SECURITY.rst
.. _style guide: https://github.com/inveniosoftware/invenio/blob/master/CONTRIBUTING.rst#commit-messages
