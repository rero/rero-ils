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
    along with this program. If not, see <http://www.gnu.org/licenses/>.

=============
Release notes
=============

v0.9.1
------

This patch is needed because `#1013`_ is missing in ``v0.9.0``, resulting in
many user interface elements that are missing.

Documentation
~~~~~~~~~~~~~

-  Updates the chart of links between RERO ILS resources.
-  Replace circulation chart with a new chart using ``dot`` from
   ``graphviz``.
-  Adds a markdown file with all circulation actions explained.
-  Adds a markdown file with scenarios based on these actions.
-  Enriches the mention of contributing libraries with UNamur and
   U.Saint-Louis Brussels (``README.rst``).

Translations
~~~~~~~~~~~~

-  Fixes a bug with the translation API that prevented exception to be
   logged.
-  Returns the source string instead of an empty string when the translation is
   missing.

Instance
~~~~~~~~

- Improves the `nginx` logs to prevents the OPTIONS requests to be logged to
  get cleaner logs in deployed instances.

Issues
~~~~~~

- `#890`__: Displays the realized actions in the circulation interface to the
  past participle, so that the librarian knows the actions are actually done.


.. _#1013: https://github.com/rero/rero-ils/pull/1013


v0.9.0
------

This release note includes the release note of ``rero-ils-ui`` version
``v0.2.0``.

User interface
~~~~~~~~~~~~~~

-  Improves the document detailed views (public and professional) with
   tabs: a “get” tab with the holdings and information on items, a
   “description” tab with extended document metadata and, in the professional
   view, an “online” tab when the resource is available through an hyperlink.
   On top of these tabs are displayed the main metadata of the document with
   the cover thumbnail.

Public interface
^^^^^^^^^^^^^^^^

-  Removes the item detailed public view which is useless, all relevant
   information being on the public document detailed view.

Professional interface
^^^^^^^^^^^^^^^^^^^^^^

-  Updates the library custom editor to normalize buttons according to the
   `charter <https://github.com/rero/rero-ils/wiki/Usability-charter#buttons>`__.
   Also, when a day is set to closed, the opening hours are hidden in addition
   to being disabled.

Search
~~~~~~

-  Moves from the ES query string, which is powerful but should not be
   used for public search input, to ES simple query, much simpler but much more
   resilient to syntax errors in the query. It also allowed to set the default
   boolean operator to AND, which is what librarians and patrons expect.
   The API requests are still done through the ES query string, as complex
   queries are needed to populate the user interface. A new HTTP query optional
   parameter is added to identify the simple query: ``&simple=1``.
-  Sets the same AND boolean operator instead of OR when selecting
   multiple items in the same facet, thus reducing the scope of the
   filter instead of expanding it.
-  Improves the ES mapping to enhance the search quality.
-  Adds a RERO ILS custom analyzer as the default analyzer.
-  Improves language analyzer with ``unicode`` capabilities (oe, œ, ue, ü,
   etc.). Uses a new ES docker image with ``icu``
   `plugins <https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-icu.html>`__
   for these functionalities.

Circulation
~~~~~~~~~~~

-  Checks that there is only one pickup location per library.
-  Processes notifications asynchronously, which is more scalable and reliable.
-  Implements *paging request to closed stack* functionality, needed and
   developed by
   `UCLouvain <https://uclouvain.be/en/libraries/about.html>`__. It
   allows to restrict, for a specific location, the available pickup
   locations, or even to disable the request option for the whole location. It
   also allows to set a manager for these paging requests, who receives
   printable email notifications for each request.

   -  Updates the location detailed view with new *paging request*
      fields.
   -  Updates the location brief view to identify the *closed stacks*. Adds
      tooltip message when the location can’t be deleted. Updates the buttons
      style according to the
      `charter <https://github.com/rero/rero-ils/wiki/Usability-charter#buttons>`__.
   -  Adapts the “request item” selector to display only the available
      pickup locations.

-  Normalizes the action buttons of the user interface according to
   the
   `charter <https://github.com/rero/rero-ils/wiki/Usability-charter#buttons>`__.

Data
~~~~

-  Updates the item JSON schema in order to remove the requirement on the
   call number. The item barcode is still required, but can be left
   empty by the librarian and be automatically set by the system.
   These changes are needed to an upcoming functionality, *receive an
   issue*, in which the librarian should be able to add an item without
   having to assign a barcode and a call number to it.
-  Creates a separate table for each resource in the database. Import
   and export of a resource are easier and access to records faster in
   big datasets.
-  Updates JSON schema to draft 7.
-  Adds methods to ensure PIDs are unique.
-  Improves JSON schema and ES mapping of the patron transaction event.
-  Implements physical description in the new data model: extent, duration,
   format, illustrations, colors and physical details.
-  Fixes creation, merging and deletion of holdings records for ebooks,
   during harvesting.
-  Links documents to person authority records through IdRef, GND or RERO
   ID instead of a MEF record ID. The MEF clustered record is still used
   to provide multilingual capabilities, but the source authority
   IDs are much more stable.
-  Updates the document editor to propose person authorities from the
   IdRef and GND records in the MEF server.

User management
~~~~~~~~~~~~~~~

-  Adds manual blocking of patrons by the librarian. Blocked patrons can’t
   check out or place requests on documents, and are informed of the
   blocking in their profile. Librarian are also informed of the blocking when
   displaying the patron profile or when trying to place circulation
   transactions that are not possible due to the blocking.

API
~~~

-  Splits the item class into two classes, the ``api.record:ItemRecord``
   to manage the item record, the ``api.circulation:ItemCirculation`` to
   manage item circulation transactions.
-  Adds a new API URL to check, when creating or updating a patron, if
   the email does not already exist. A validation message is displayed
   in the editor.
-  Exposes PO based translations in JSON through a new API HTTP endpoint
   to the angular application (``rero-ils-ui``), to avoid translating
   the same strings in both projects. On the ``rero-ils-ui`` side, the
   translation mechanism is updated to consume the exposed JSON file
   translations.
-  Adds ``create`` to the permission API and removes permissions from
   the ``SearchSerializer``.
-  Improves the way ``rero-ils-ui`` gets permissions, through the
   permission API instead of a search query.

Documentation
~~~~~~~~~~~~~

-  Adds an informative ``README.rst``, addressed to the general public and
   developers, explaining the context of the project, what it does and is going
   to do, where to find documentation on how to develop, install or contribute
   to RERO ILS.
-  Updates the ``rero-ils-ui`` issue template in order to remind users to
   privilege issue creation in the ``rero-ils`` GitHub repository.

Tests
~~~~~

-  Fixes another dependency issue, this time with ``jsonresolver``.
-  Fixes ``pytest-invenio`` version ``1.2.2`` breaking tests, because it
   downgrades ``pytest-flask`` and ``Flask``. ``pytest-invenio`` is
   pinned to ``1.2.1``.
-  Fixes unit tests for item barcode automatically generated (prefixed
   with “f-”), to ensure that the time stamp of the generated barcode
   equals the ``sysdate`` time stamp.
-  Tests the ES simple query with provided search use case in different
   languages.
-  Installs, configures and adds first Cypress test for end to end (e2e) tests.

``rero-ils-ui``
~~~~~~~~~~~~~~~

-  Rewrites ``MainTitleService`` as a pipe to ease its use in
   components.
-  Fixes the test component name to be coherent with component name.
-  Rewrites tests to limit imports and declarations.
-  Fixes private attribute names that were missing the leading
   underscore.

Instance
~~~~~~~~

-  Moves from ``pipenv`` to ``poetry`` to improve dependency
   management. Uses ``python-dotenv`` to load ``.env`` and ``.flaskenv``
   files. This allowed to upgrade ``werkzeug`` which resulted in an
   issue fixed with the item view and the tests.
-  Removes a bad hack with ``appnope`` package for Mac OSX.
-  Removes ``setuptools`` manifest which is not used anymore.
-  Configures ``celery`` to load ``.env`` and ``.flaskenv`` files.
-  Adds ``invenio-logging`` Sentry extensions.
-  Removes ``pipenv`` environment variables from the ``setup`` script.
-  Fixes an error when interrupting the ``server`` script, resulting in
   processes still running, after the move from ``pipenv`` to
   ``poetry``.
-  Improves the handling of scheduled tasks with the use of REDIS
   scheduler backend, allowing to enable, disable, update, create
   scheduled tasks dynamically.

Issues
~~~~~~

-  `#91 <https://github.com/rero/rero-ils/issues/91>`__: The facets
   behaviour was not as expected. It associated two items with an OR instead of
   an AND operator.
-  `#675 <https://github.com/rero/rero-ils/issues/675>`__: A question
   was raised on how to improve the library custom editor, specifically the
   opening hours section. It was decided to hide the opening hours for
   closed days.
-  `#755 <https://github.com/rero/rero-ils/issues/755>`__: The search
   failed with a query containing brackets ``[]``.
-  `#819 <https://github.com/rero/rero-ils/issues/819>`__: The
   population of items in editor selectors was very slow.
-  `#850 <https://github.com/rero/rero-ils/issues/850>`__: Creation of
   two records with the same PID is possible.
-  `#884 <https://github.com/rero/rero-ils/issues/884>`__: Removes the
   public item detailed view as it is not useful anymore.
-  `#890 <https://github.com/rero/rero-ils/issues/890>`__: Actions
   realised in circulation should be in past participle, not in the
   infinitive form.
-  `#932 <https://github.com/rero/rero-ils/issues/932>`__: Librarians were able
   to edit item types and patron types, but these actions should be reserved to
   system librarians.
-  `#934 <https://github.com/rero/rero-ils/issues/934>`__: Searching for
   patrons in a large data set should rely on a good ranking, in order
   to get an exact match on the top of the results page.
-  `#1000 <https://github.com/rero/rero-ils/issues/1000>`__: A test on
   the document API was not raising exceptions, resulting in a failed test.

v0.8.0
------

This release note includes the release note of ``rero-ils-ui`` version
``v0.1.2``.

User interface
~~~~~~~~~~~~~~

-  Implements gradually the `graphic charter specifications for buttons <https://github.com/rero/rero-ils/wiki/Usability-charter#buttons>`__.
-  Launches a search when the user clicks on a title suggestion in the
   search bar, directly.

Professional interface
^^^^^^^^^^^^^^^^^^^^^^

-  Filters search results by organisation to focus on the most useful
   content for the librarian.
-  Filters by organisation also the search suggestions.
-  Adds the librarian organisation as a parameter in the hyperlink of the
   document title in the brief view (search result list).
-  Adds a history tab in the patron profile to display the loan history of the
   last 6 months.
-  Updates the patron type detailed view with new subscription fields.
-  Adds a holdings record editor to define:

   -  Publication patterns.
   -  Prediction preview templates.

-  Supports three different types of holdings record in the document detailed
   view:

   -  Standard with the add/edit buttons to load the item editor.
   -  Electronic with no action available (replaces the ``harvested``
      property mechanism).
   -  Serial with the add/edit buttons to load the holdings record editor.

-  Adds IdRef persons in the person search (adapts search suggestions and
   person brief view).
-  Implements the requests and request queue edition, allowing the
   librarian to add a new request to the queue or to edit an existing
   request (deleting it, or updating the pickup location).

Circulation
~~~~~~~~~~~

-  Adds the responsibility statement to the title in the notification
   sent to the patron.
-  Uses the pickup location email as sender for the notification email.

User management
~~~~~~~~~~~~~~~

-  Implements the subscription functionality, so that patrons of a
   specific patron type will receive an annual fee to subscribe to the
   library services.
-  Creates the subscription at patron creation or update if needed
   (depending on the patron type).
-  Implements scheduled tasks to:

   -  Clean old subscriptions.
   -  Create new subscriptions for patrons linked to a patron type with
     a subscription but that are missing the subscription fee.

-  Displays an alert to the patron, in the patron profile for pending
   subscription.

Metadata and data
~~~~~~~~~~~~~~~~~

-  Improves harvesting of ebooks metadata from external commercial
   platform, avoiding to stop the harvesting when it encounters faulty
   data.
-  Displays IdRef as a source in the person detailed view, as IdRef has
   been added to the MEF server
   (`rero/rero-mef@7d8a7467 <https://github.com/rero/rero-mef/commit/7d8a746750c92767672aaef04c8a7d628391bb5e>`__).
-  Displays bibliographic metadata in the fee history only when relevant
   (ie ovedue transaction).
-  Improves document JSON schema according to the
   `guidelines <https://github.com/rero/developer-resources/blob/master/guidelines/json-schemas.md>`__.

Search
~~~~~~

-  Adapts indexer to new possibilities offered by Invenio 3.2, such as
   indexer class, which allows the ``IlsRecordIndexer`` to be
   simplified.

Acquisition
~~~~~~~~~~~

-  Begins to implement serial management with the creation of a manual
   prediction:

   -  Adds a ``holdings_type`` parameter to the holdings record to
      differentiate standard records (ie monographs), electronic records or
      serials.
   -  Updates the JSON schema of the holdings record to:

      -  Configure the holdings record editor, in which the publication
         pattern will be defined.
      -  Encode the publication pattern in the holdings records.

   -  Computes predicted issues preview based on the publication pattern of a
      given holdings record.
   -  Implements a template mechanism to configure how the issue of a
      given pattern is displayed.

API
~~~

-  Improves the permission API and configuration to ensure that some
   resources can only be updated by a system librarian.
-  Allows the organisation record to be updated. This is needed to allow
   system librarians to edit the link from an acquisition account to a
   budget.
-  Adds a route to update the pickup location of an existing request.

Fixtures
~~~~~~~~

-  Regenerates documents and holdings records after the changes for the serials
   predictions.
-  Adds in the fixtures the 10 publication patterns that are currently most
   used in the RERO network.

Tests
~~~~~

-  Uses ``pipenv run safety check`` instead of ``pipenv check`` to avoid
   a temporary issue with ``pipenv``.
-  Increases test coverage in the location module.
-  Fixes ``pytest-invenio`` static path location. A PR is pending on the
   ``pytest-invenio`` project.
-  Many fixes due to dependencies issues.

Scripts
~~~~~~~

-  Allows the ``setup`` script to succeed even if records don’t have any
   ``responsibilityStatement``.

Instance
~~~~~~~~

-  Updates Invenio framework to version ``3.2.1``!
-  Upgrades ``https-proxy-agent`` for security reasons.
-  Uses ``rero-ils-ui`` version ``v0.1.2``.

Documentation
~~~~~~~~~~~~~

-  Updates the PR templates to add a section on cross dependencies
   between ``rero-ils`` and ``rero-ils-ui`` projects.

Issues
~~~~~~

-  `#788 <https://github.com/rero/rero-ils/issues/778>`__: The search
   suggestions are displayed only after a click in the input field, even
   after 3 typed characters.
-  `#939 <https://github.com/rero/rero-ils/issues/939>`__: The email
   notification should use the email of the library as sender.
-  `#960 <https://github.com/rero/rero-ils/issues/960>`__: A librarian
   using the web browser Chrome/Chromium wasn’t able to update the
   pickup location of a request.
-  `rero/rero-ils-ui#140 <https://github.com/rero/rero-ils-ui/issues/140>`__:
   the library facet was missing in the professional interface.

v0.7.0
------

User interface
~~~~~~~~~~~~~~

-  Moves to ``rero-ils-ui`` version 0.1.0. ``rero-ils-ui`` is the
   angular project for part of the user interface (public search and
   professional interface).
-  Fixes some issues in the source code identified through the
   translation process (in both projects: ``rero-ils`` and
   ``rero-ils-ui``).

Public interface
^^^^^^^^^^^^^^^^

-  Improves request deletion by patron, to keep the request tab
   active after deletion.
-  Fixes the cover image display in the document detailed and brief view
   of the public interface.
-  Displays the document title field in brief and detailed views.
-  Adapts the configuration of the search views to be compatible with
   ``ng-core``, in order to ensure that professional action buttons do
   not appear on the public interface.

Professional interface
^^^^^^^^^^^^^^^^^^^^^^

-  Adds examples in the placeholders in the patron editor.
-  Adds a request button on the document detailed view, that allows a
   librarian to place a request on an item on behalf of a patron. The
   button opens a modal in which the librarian can scan a patron barcode
   and select a pickup location.
-  Truncates the abstract in the document detailed view and adds a *show more*
   link to get the complete abstract. This uses a ``ng-core`` component.
-  Fixes the messages displayed to the librarian as he or she’s placing
   a request on an item for a patron.
-  Centralizes useful data to populate the professional interface front
   page board and menu.
-  Improves information about unavailable items on the item detailed
   view.
-  Displays the electronic location on the document detailed view.
-  Displays the document title field in brief and detailed views.
-  Improves the edition statement field display on the document detailed
   view.
-  Implements the fee tab of the patron account from the librarian point
   of view.
-  Fixes uniqueness value check of several fields in the location
   record, such as ``is_online``, ``pickup_name``, etc., when a location
   is created or updated.
-  Adds guards to protect access to any resource editor based on the
   user permissions. A basic error page is also added.
-  Removes the location from the library brief view (search result) and
   moves it to the library detailed view.
-  Hides the action button on the location detailed view depending on the
   user permission on the library (the parent record).

Circulation
~~~~~~~~~~~

-  Generates fees (“patron transactions”) and “patron transaction
   events” when a loan is overdue.
-  Returns all applied actions after a successful checkin ou checkout,
   in order to address new circulation use cases.

User management
~~~~~~~~~~~~~~~

-  Adds a new resource, “patron transaction”, to manage all the
   different fees that a parton will generate (overdue checkout,
   photocopy, subscription, lost or damaged item, interlibrary loan,
   etc.)
-  Adds a new resource, “patron transaction event” to track the history
   of each fee (partially paid, paid, disputed, etc.)
-  Adapts the “fee” resource to make use of “patron transaction” and
   “patron transaction event” resource.
-  Allows the librarian to register payment or partial payement for fees.

Metadata
~~~~~~~~

-  Implements the ``electronicLocator`` fields in the metadata model.
-  Implements the ``title`` fields in the metadata model, with transformation
   from RERO MARC21 and BNF UNIMARC, which was a huge work.
-  Improves the ``marc21json`` CLI to enable debugging options.
-  Updates the location JSON schema to make the ``pickup_name`` field
   required if the location is a pickup location (``is_pickup`` is set
   to ``true``).
-  Updates the document records to the new MEF IDs.
-  Checks and removes leading or trailing spaces in the item and patron
   barcodes.

Acquisition
~~~~~~~~~~~

-  Adds “invoice” resource. This resource is linked to the “vendor”
   resource.
-  Removes useless functions in the "order line" ressource.

API
~~~

-  Adds a sort function on pickup name location.
-  Checks if the librarian has the permission to place a request on an
   item for a patron.
-  Adds the possibility for a librarian to place a request on an item
   for a patron.

Fixtures
~~~~~~~~

-  Adds patron transaction and patron transaction event fixtures.
-  Adds loan fixtures to create active and paid overdue fees.

Tests
~~~~~

-  Fixes issue with the daylight saving timezone that occurs twice
   a year.
-  Fixes other timezone issues and displays better error messages. Tests
   for the circulation backend are highly dependent on a good timezone
   management.
-  Compares library opening hours in UTC only, to avoid changing
   daylight saving timezones.
-  Removes solved security exception and adds a new one on ``pipenv``.
-  Adds a new ``live_server_scope`` option in ``pytest.ini`` due to the
   new ``pytest`` version (``1.1.0``).
-  Set ``bleach`` version to ``>=3.1.4`` to fix a ReDOS security breach.
-  Pins the ``SQLAlchemy`` version to ``1.3.15`` because the last
   version breaks the tests.

Instance
~~~~~~~~

-  Adds in the utilities scripts a method to get the JSON reference
   corresponding to a given PID.
-  Improves dependencies declaration in the ``Pipfile`` to reduce
   dependency conflicts and documents the ``Pipfile`` accordingly.
-  Starts BASH scripts with ``pipenv run`` (bootstrap, console, server,
   setup, update).
-  Adds support for newer version of the python import order check tool
   (``isort`` >= ``4.3.10``).
-  Fixes the DB identifier sequence computation.
-  Monitors data consistency between the DB and the indexes. That is
   useful to be aware of issues in a deployed instance.
-  Pins the ``bleach`` version to fix a XSS security breach.
-  Fixes a useless ``tgz`` file installation in the ``bootstrap``
   script.
-  Removes wrong parameters to the bootstrap script (``-s`` and ``-b``).
-  Updates ``PyYaml`` to fix a vulnerability (CVE-2020-1747).
-  Adds a script to check circulation dates (due date) through a
   complete year, to identify all timezone issues.
-  Rename ``rero-ils-ui`` checkout component to checkin according to
   its usage.
-  Update dependencies for security reasons: ``minimist``, ``acorn``,
   ``kind-of``.

Documentation
~~~~~~~~~~~~~

-  Updates installation procedure with instruction to set the correct
   version of ``pipenv`` and ``python``.
-  Adds a flask ``Flask-Wiki`` module to display and edit help
   documentation for the end users.
-  Updates the contributors list of the ``rero-ils-ui`` project.

Issues
~~~~~~

-  `rero-ils-ui#169 <https://github.com/rero/rero-ils-ui/issue/169>`__:
   A CSS styling rule was missing on the person detailed view of the
   professional interface to reduce the size of the source information
   badges.
-  `rero-ils-ui#209 <https://github.com/rero/rero-ils-ui/issue/209>`__:
   In the patron account fee tab of the professional interface, the
   actions drop down menu was not placed just below the action button.
-  `#538 <https://github.com/rero/rero-ils/issue/538>`__: Help messages
   (ie JSON schema description fields or validation messages) were
   missing in the patron editor.
-  `#575 <https://github.com/rero/rero-ils/issue/575>`__: The library
   editor was accessible to any librarian typing the correct URL in the
   web browser. The record couldn’t be saved, but still.
-  `#787 <https://github.com/rero/rero-ils/issues/787>`__: As a
   generalization of issue
   `#575 <https://github.com/rero/rero-ils/issue/575>`__, access to
   resources editor had to be protected based on the user permissions.
-  `#793 <https://github.com/rero/rero-ils/issues/793>`__: In some
   cases, the patron displayed in the checkin interface wasn’t correct.
   To solved this, better information had to be returned after the
   checkin.
-  `#794 <https://github.com/rero/rero-ils/issues/794>`__: The
   ``pickup_name`` field of a location that is pickup wasn’t required,
   thus resulting in incomplete records when creating or updating a
   location through the editor.
-  `#798 <https://github.com/rero/rero-ils/issues/798>`__: The
   professional item detailed view didn’t display information on why an
   item isn’t available in some cases.
-  `#803 <https://github.com/rero/rero-ils/issue/803>`__: In the request
   validation interface, when the librarian validated a request, the
   focus form the input field was lost, forcing the librarian to click
   to set the focus for the next validation.
-  `#804 <https://github.com/rero/rero-ils/issue/804>`__: Example had to
   be added in the patron editor to help the end user.
-  `#826 <https://github.com/rero/rero-ils/issue/826>`__: In the checkin
   interface, when a checkin item has a request, the name of the patron
   that placed the request was not displayed in the correct order (last
   name, first name).
-  `#827 <https://github.com/rero/rero-ils/issue/827>`__: The component
   alignment in the circulation interface had to be improved. Items
   with an action button were shorter than items without any button.
-  `#829 <https://github.com/rero/rero-ils/issue/829>`__: Some flash
   messages were missing when the librarian is checkin in items that have
   requests, or fees, or that should be sent in transit.
-  `#830 <https://github.com/rero/rero-ils/issue/830>`__: In the
   circulation interface, the name of some pickup location had an extra
   trailing space, that had to be removed.
-  `#856 <https://github.com/rero/rero-ils/issue/856>`__: The bootstrap
   script was trying to install ``rero-ils-ui`` from the ``tgz`` file
   even if the ``-t`` option was not used.

v0.6.1
------

Instance
~~~~~~~~

- Uses `rero-ils-ui` version `0.0.12`.

Documentation
~~~~~~~~~~~~~

- Adds the missing  release notes and changelog.

Issues
~~~~~~

-  `rero/rero-ils#775 <https://github.com/rero/rero-ils/issues/775>`__:
   when using the *switch library* toggle, the list of requested items
   wasn't updated, so a wrong list was proposed to the librarian.
-  Fixes a typo in `cli.py`.

v0.6.0
------

User interface
~~~~~~~~~~~~~~

-  Adds a “renew” button in the patron profile, to allow the patron to
   renew the borrowed item, if possible (no request on it).
-  Re-enables autocomplete in the search input.
-  Splits the user interface into a public interface and a
   professional interface (ie for librarians).
-  Removes all professional actions from the public interface, as they
   are moved to the professional interface.
-  Moves all professional functionalities to a dedicated angular
   application.
-  Adds a link to switch to the professional interface (only available
   to logged in librarians).
-  Adds a link to switch from the professional interface to the public
   interface.
-  Filters persons by organisation views.
-  Changes the angular library to generate forms (form
   `angular6-json-schema-editor <https://github.com/hamzahamidi/ajsf>`__
   to `ngx-formly <https://github.com/ngx-formly/ngx-formly>`__), in
   order to accommodate the need for a complex cataloging editor.
-  Displays custom logos and header color for each organisation and for the
   professional interface.
-  Adds a “history” tab in the patron profile to display the transaction
   history of the last 6 months.
-  Adds a button in the requests tab of the patron profile to allow
   patrons to cancel their own requests.
-  Updates the frontpage for the pilot libraries instance, with relevant
   information.
-  `[rero-ils-ui] <https://github.com/rero/rero-ils-ui>`__ Improves the
   circulation module user interface with better information display (for
   requests, transit and fees) and automatic performance of transactions.
-  `[rero-ils-ui] <https://github.com/rero/rero-ils-ui>`__ Implements the
   patron account view in the professional interface, with tabs for checked
   out items, requests, fees and personal information.

Search and indexing
~~~~~~~~~~~~~~~~~~~

-  Improves ebook bulk indexing (``invenio utils reindex``,
   ``invenio utils runindex``).
-  Improves person indexing during document indexing and document
   creation.
-  Fixes missing mappings in JSON schemas.
-  Adds default sorting for each resource.

Circulation
~~~~~~~~~~~

-  Takes into account library timezone for all circulation transactions.
-  Links loans and fees through the notification resource.
-  Enriches fee index with ``loan.pid``, ``patron.pid`` and
   ``organisation.currency``.
-  Adds an order parameter to sort pending loans.
-  Improves the method for finding the correct location of an item when it
   is in circulation.

Metadata
~~~~~~~~

-  Improves ``dojson`` transformations (MARC21 to JSON), especially the
   ability to do parallel transformations, which is necessary for
   complex tasks.
-  Updates and improves UNIMARC ``dojson`` transformation (BnF
   importation).
-  Adds a comprehensive language list to the document JSON schema.
-  Reserves ranges of PIDs, useful to import linked resources from external
   systems.
-  Adds a dump function to compute an unstructured ``_text`` field based on
   structured data. This field is for display purposes. This new field is also
   added to the JSON schema.
-  Adds a dump function to items, to populate items index with
   organisation, location and availability data.
-  Fixes document dumps for records without series.
-  Fixes ``dojson`` series field transformation for ebooks.
-  Adds a CLI command to automatically translate the LoC language list.
-  Implements and rewrites ``provisionActivity`` field in the new data model
   and adapts the needed transformations.
-  Fixes ``provisionActivity`` ``startDate``.
-  Implements edition statement field in the new data model and the
   needed transformations.
-  Adds a command to the bootstrap script to compile JSON (JSON
   references for definitions).
-  Improves performance with MEF person importations:

   -  Imports MEF persons in the DB, not only in ES.
   -  Reduces the number of requests to the DB and ES.

-  Updates JSON schemas to the new ``ngx-formly`` library (form options
   are now directly in the schema).
-  Sets the document abstract field to ``textarea`` type.

Acquisition
~~~~~~~~~~~

-  Adds new resources for vendor file, orders and order lines.
-  Adds new resources for organisation acquisition budget and library
   acquisition account.
-  Inherits the acquisition account currency from organisation default
   currency.
-  Prevents deletion of acquisition account if orders are linked to it.
-  Enriches the organisation record by the ``current_budget_pid``.
-  Sets the budget dates field to ``date`` instead of ``datetime``.
-  Links order lines to documents.

API
~~~

-  Restricts actions on items to the librarians working at the owning
   library.
-  Allows read access to holdings and items for all users.
-  Adds access to loan API for users of the same organisation.
-  Restricts patron API loan search to their own loans.
-  Sets loan API search sort order to loan’s ``transaction_date``.
-  Limits edit, delete and update actions on acquisition account to
   librarians of the same library.
-  Allows librarians to read acquisition budgets of their library.
-  Allows system librarians to create, edit, delete, update acquisition
   budgets and accounts at the organisation level.
-  Blocks deletion of the organisation’s current budget.
-  Allows system librarians to edit the parameters of their own
   organisation.
-  Sets permissions for orders and order lines.
-  Moves update and delete permissions from serializer to API.

Fixtures
~~~~~~~~

-  Fixes the numbers of items generated.
-  Improves error handling and logging for JSON reference resolvers.
-  Adds lazy record creation option to the setup.
-  Sets opening of the third organisation libraries to 01:00 AM, because
   the editor does not validate with an opening hour set to 00:00.
-  Adds a CLI and a configuration file to test the PID dependencies in
   the fixture data (ie relations between resources).
-  Adds vendor fixtures.
-  Adds acquisition budgets and acquisition accounts fixtures.
-  Improves notification fixtures with ``due_soon`` and recall records.
-  Exports existing MEF persons from a running instance and then imports
   persons when building another instance, in order to speed up the setup.

Tests
~~~~~

-  Adds PID verification with commit/rollback.
-  Improves test coverage with mef-persons tasks, ebooks receivers, API
   harvester.
-  Updates ``.run-tests.sh`` to ``pytest`` 5.3.3.
-  Improves the license check.

Instance
~~~~~~~~

-  RERO ILS is now three different projects, three different git
   repositories:

   -  The repository `rero-ils <https://github.com/rero/rero-ils>`__
      contains the backend, the Invenio instance and the flask
      application.
   -  `ng-core <https://github.com/rero/ng-core>`__ is an angular
      library for a User Interface, shared between two RERO projects
      based on Invenio, RERO ILS and `SONAR <https://sonar.ch>`__.
   -  `rero-ils-ui <https://github.com/rero/rero-ils-ui>`__ contains two
      angular applications, one for the public search interface, the
      other one for the professional interface.

-  Uses ``invenio-assets`` (``NpmBundle``) to integrate angular apps and
   removes ``webpack`` command in the bootstrap script.
-  Adds the possibility to install ``rero-ils-ui`` from a locally
   generated ``.tgz``.
-  Adds a variable in ``bundles.py`` to set ``rero-ils-ui`` version.
-  Updates ``Dockerfile`` to use ``rero-ils-ui`` package file.
-  Adds ``rero-ils-ui`` version or commit hash on
   `ilsdev.test.rero.ch <https://ilsdev.test.rero.ch>`__ frontpage.
-  Improves scripts:

   -  ``run-tests.sh``.
   -  speeds up ``scripts/setup`` and cleans unnecessary warnings.
   -  ``scripts/bootstrap``.

Documentation
~~~~~~~~~~~~~

-  Improves templates for GitHub pull request, in order to remind
   developers to check if strings to be translated have correctly been
   extracted.
-  Documents links between RERO ILS resources in
   ``doc/reroils_resources.*`` files.

Issues
~~~~~~

-  `#571 <https://github.com/rero/rero-ils/issues/571>`__: the string
   “not extendable” was not translated in the notifications templates.
-  `#574 <https://github.com/rero/rero-ils/issues/574>`__: librarians
   could edit items belonging to other libraries.
-  `#550 <https://github.com/rero/rero-ils/issues/550>`__: person
   result list should be filtered by the organisation view.
-  `#552 <https://github.com/rero/rero-ils/issues/552>`__: after
   deleting a document, a *page not found* was presented to the user.
   This fix provides a confirmation message and redirects the user to
   the list of documents.
-  `#572 <https://github.com/rero/rero-ils/issues/572>`__: some strings
   in the patron editor were not correctly translated.
-  `#599 <https://github.com/rero/rero-ils/issues/599>`__: due date
   computation resulted in wrong output, due to incomplete timezone
   support.
-  `#601 <https://github.com/rero/rero-ils/issues/601>`__: deleting a
   document resulted in an exception, because a non existing linked
   ``mef_reference`` could not be deleted.
-  `#213 <https://github.com/rero/rero-ils/issues/213>`__: needs a
   method to validate circulation policies when they are imported and
   not created through the editor.
-  `#625 <https://github.com/rero/rero-ils/issues/625>`__: the
   circulation policy custom editor didn’t display selected policy
   settings (to which patron types and item types the policy applies
   to).
-  `#626 <https://github.com/rero/rero-ils/issues/626>`__: an error in
   circulation policies data prevented the second organisation system
   librarian to edit circulation policies.
-  `#646 <https://github.com/rero/rero-ils/issues/646>`__: the French
   translation of system librarian wasn’t correct on the frontpage.
-  `#770 <https://github.com/rero/rero-ils/issues/770>`__: the
   destination of an item in transit was not displayed correctly after a
   checkin.
-  `#776 <https://github.com/rero/rero-ils/issues/776>`__: item
   information in the holding displayed the library code, which is not
   relevant. The library name and location name are the desired
   information to be displayed here. The destination of an item in transit
   was not displayed correctly after a checkin.
-  `#777 <https://github.com/rero/rero-ils/issues/777>`__: the item
   request button should be populated by pickup location names instead
   of library names.
-  `#780 <https://github.com/rero/rero-ils/issues/780>`__: checkin of
   requested items resulted in the wrong transit destination. This was
   due to a bug in the ``invenio-circulation`` version used by RERO ILS.
   Temporarily, the circulation transitions have been overwritten.
-  `rero/rero-ils-ui#76 <https://github.com/rero/rero-ils-ui/issues/76>`__:
   it should be possible to delete a circulation policy even if it
   contains parameters.

v0.5.2
------

-  User interface:

   -  Fixes user initials display in the user menu.
   -  Fixes the extended facet items number which was troncated due to
      REST API configuration.

-  Editor:

   -  Fixes item type validation.
   -  Fixes validation message for patron phone number.
   -  Fixes ``dojson`` transformation from unimarc to JSON to prevent
      poor ``provisionActivity`` field implementation (WIP) to break BnF
      imported records to be submitted through the editor.

-  Circulation:

   -  Always cancels active loan when the check-in item has pending
      requests on it.
   -  Sets loan ``transaction_date`` to ``datetime.now(utc)``.
   -  Filters circulation policies by organisation.

-  Fixtures:

   -  Adds opening hours for the third organisation libraries.
   -  Adds libraries, librarians, locations, patrons, items and
      transactions in the third organisation for the workshops.

-  Issues:

   -  `#598 <https://github.com/rero/rero-ils/issues/598>`__: fixes
      population of the request button when there’s no pickup location
      in a library, as a patron load a document detailed view.
   -  `#607 <https://github.com/rero/rero-ils/issues/607>`__: fixes
      importation from BnF server. Logs have been improved.
   -  `#608 <https://github.com/rero/rero-ils/issues/608>`__: fixes the
      reset password link sent to a patron created by a librarian. To do
      this, the RERO ILS templates for ``flask-security`` have to be
      loaded before the ``falsk-security`` templates.
   -  `#609 <https://github.com/rero/rero-ils/issues/609>`__: fixes an
      error in the document JSON schema that prevent to add an author in
      the editor, when no author field is activated.

v0.5.1
------

-  User interface:

   -  Adds a new method to change session locale, in preparation for the
      future pure JS application.
   -  Rewrites frontpage to emphasize the public demo site and improves
      its rendering on small screens.
   -  Improves the search input suggestion UX.

-  Fixtures: updates the third organisation default circulation policy
   for the workshops.
-  Documentation:

   -  Improves the github issue template with information on the
      instance and version of RERO ILS on which the issue occurred.

-  Fixed issues:

   -  `#488 <https://github.com/rero/rero-ils/issues/488>`__: disallows
      editing libraries by a non affiliated librarian.
   -  `#475 <https://github.com/rero/rero-ils/issues/475>`__: redirects
      homepage to the global view.
   -  `#540 <https://github.com/rero/rero-ils/issues/540>`__: helps
      distinguish "organisation" from "organisation" as an author in order
      to ease translation.
   -  `#573 <https://github.com/rero/rero-ils/issues/573>`__: rename
      locations incorrectly labelled as online.
   -  `#232 <https://github.com/rero/rero-ils/issues/232>`__: improves
      position of flash messages in order to always show  on the screen, even
      if the screen is scrolled down.
   -  `#556 <https://github.com/rero/rero-ils/issues/556>`__: fixes a
      wrong label field in the ``identifiedBy`` field.
   -  `#557 <https://github.com/rero/rero-ils/issues/557>`__: fixes a
      bug in the document editor which was preventing the submit button
      to be activated.
   -  `#562 <https://github.com/rero/rero-ils/issues/562>`__: fixes a
      bug in the location editor which was preventing the submit button
      to be activated.
   -  `#404 <https://github.com/rero/rero-ils/issues/404>`__: fixes
      internationalization code in the source in order to make it
      translatable.
   -  `#553 <https://github.com/rero/rero-ils/issues/553>`__: fixes
      wrong filter on persons detailed views to restore the list of
      related documents.
   -  `#560 <https://github.com/rero/rero-ils/issues/560>`__: makes sure
      fees are indexed in ElasticSearch.

v0.5.0
------

-  User interface:

   -  Document availability:

      -  Replaces status by availability in item detailed views.

   -  Improves button hiding approach on the document detailed view of
      harvested ebooks.
   -  Development instance: displays deployed commit hash on the frontpage,
      in order to better identify which code is deployed.

-  Data model:

   -  Automatically creates holdings for harvested documents, ie ebooks:

      -  Adds an *online* type to the item type resource.
      -  Adds a ``is_online`` flag to the location resource.
      -  Adds an ``online_harvested_source`` to the organisation
         resource.
      -  Displays holdings data for harvested ebooks on document
         detailed views.

-  Circulation:

   -  Fees:

      -  Adds a new *fee* resource.
      -  Sets default currency at the organisation level.
      -  Adds a new field to the circulation policy editor:
         ``overdue fees amount``.
      -  Updates the circulation policies editor with overdue fees
         amount field.

-  Search:

   -  Enables bulk indexing for harvested ebooks.

-  Fixtures:

   -  Adds an *online* location for *online* documents (only one per library).
   -  Adds an *online* item type.
   -  Adds circulation policies for ebooks, in order to disallow
      circulation for *online* documents.
   -  Adds data for a third organisation, to be use during workshops.

-  Tests:

   -  Improves tests writing with ``postdata()`` instead of
      ``client.post()`` to reduce the number of POST requests.

-  Documentation: now updates ``CHANGES.rst`` and
   ``RELEASE-NOTES.rst`` files.
-  Instance:

   -  Updates Elastiscearch and Kibana to 6.6.2

-  Fixed Issues:

   -  `#363 <https://github.com/rero/rero-ils/issues/363>`__: structures
      editor with section.
   -  `#405 <https://github.com/rero/rero-ils/issues/405>`__: increases
      API size limit to allow loading many circulation policies in user
      interface.
   -  `#462 <https://github.com/rero/rero-ils/issues/462>`__: fixes
      wrong state attributed to an item belonging to organisation B
      checked in organisation A.
   -  `#547 <https://github.com/rero/rero-ils/issues/547>`__: fixes JSON
      export.
   -  `#563 <https://github.com/rero/rero-ils/issues/563>`__: resets
      database sequence to correct value after loading records.

v.0.4.0
-------

-  Data model:

   -  Adds holdings level, to gather items data from the same
      circulation category and location.

      -  As the librarian adds an item to a document, the holdings is
         automatically created, based on item type and location.
      -  Then, new items are automatically attached to a holdings.
      -  As the last item of a holdings is deleted, the holdings is
         automatically deleted.
      -  As an item is updated, changing its type or location, the
         holdings is updated accordingly, meaning that it can be deleted
         and another one created.
      -  Avoids holdings automatic creation for fixture, otherwise it
         slows to much the fixture population.

   -  Implements new field in the data model: copyright date.
   -  Implements new field in the data model: publication statement.
   -  Improves the ``dojson`` utility to allow multiple visits of the
      same source field or zones for a single transformation.

-  User interface:

   -  Improves availability display for document, holdings and items, in
      document brief and detailed views
   -  On document detailed views, holdings are displayed with holdings
      and item data.
   -  In an organisation’s view, documents are filtered using holdings
      data.

-  Record editor, specifically for cataloging usage:

   -  Compacts the layout and improves the user interface look.
   -  Allows to add and remove first level fields that are not required.
   -  When updating an existing record or when importing a record,
      populated fields are displayed with data, but empty fields are
      hidden.
   -  When using the async validator, ie to check the uniqueness of item
      barcodes, the submit button is disabled.

-  Circulation:

   -  Circulation policies get item data from the holdings.
   -  Invenio logger message for item API added to circulation user
      interface, and improvement of error message provided to the
      librarian.

-  Harvested documents:

   -  Improves the ES indexing of OAI-PMH harvested records.

-  Fixtures:

   -  Renames fixture files from 10k or 1k to ``big`` and ``small``, and
      reduces the size of fixture data to speed up the development
      setup.
   -  Reduces missing items to 2%.
   -  Extends the set of supported document languages, in order to allow
      the new data model to be tested.
   -  Updates data with updated MEF data.

-  Tests:

   -  Adds a script to test the license headers for all concerned files.
   -  Cleans tests fixture data.

-  Instance:

   -  ``bootstrap`` script:

      -  Uses always ``pipenv npm`` instead of system ``npm``.
      -  Removes unnecessary ``virtualenv``.
      -  Improves output message colors.

   -  Adds a ``validate`` command to the CLI to allow manual validation
      of a record against a JSON schema.
   -  Standardizes timezone globally, using utc timezone in all cases.

-  Documentation:

   -  Moves the existing issue template to default issue template.
   -  Adds a pull-request template with a checklist for code reviewers.

-  Fixed issues:

   -  #437: restores the display of field “note” in the document
      detailed view.
   -  #390: fixes the edit button in the document detailed view and in
      the professional document brief view, complying with the view
      filter for organisations.
   -  #389: selects the affiliation organisation of the librarian in the
      edition form.
   -  #223: improves the user interface of library calendar exceptions.
   -  #366: improves the text displayed in the tabs of the circulation
      user interface.
   -  #377: applies organisation filter on circulation user interface to
      avoid processing items and patrons from other organisations.
   -  #447: fixes missing message on item delete button in document
      detailed views.
   -  #225: fixes user menu sometimes not displaying user initials.
   -  #495: fixes display of default thumbnail icon on document and item
      detailed views.
   -  #484: fixes unnecessary loan creation.
   -  #381: improves front page display in small screens.

v.0.3.1
-------

Fix missing strings translations.

v.0.3.0
-------

Starting metadata and views

-  User interface:

   -  Add the language facet translations.
   -  Add a button to expand or shrink the number of facet items
      displayed.

-  Circulation:

   -  Notifications are based on templates for the different languages
      and communication channels.
   -  Upgrade ``invenio-circulation`` from ``v1.0.0a14`` to
      ``v1.0.0a16``

-  Search and indexation:

   -  Revert to default boolean OR operator and set the ranking order.
   -  Add a new ``display_score=1`` URL parameter to display the ES
      (Elasticsearch) score, in order to improve ES debugging or
      configuration.
   -  Improve ES mappings and JSON Schemas for documents:

      -  Documents have two schemas, one for harvested data, one for
         internal records.
      -  eBooks no longer have their own mapping in order to have a
         single mapping for all documents (to make searching
         consistent).

   -  Add indexation class property to ``IlsRecords``, in order to get a
      different indexer for each resource.

-  Data model:

   -  Implement new data model for ``identifiedBy`` and ``language``:

      -  ``dojson`` transformation from MARC21.
      -  Update JSON Schema and ES mappings.
      -  Update user interface views and editor.

-  Consortium:

   -  Implement views by organisations and a global one, with content
      filtered by the URL parameter.

-  Tests:

   -  Extract external service tests to a specific test battery.
   -  The external service tests are made optional in the
      ``run-tests.sh`` script.
   -  Rewrite ``Pipfile`` to ensure a clean dependencies graph.

-  Instance:

   -  Upgrade to Invenio 3.1.1 (security updates).
   -  Replace the deprecated ``invenio-records`` CLI by a
      ``invenio fixtures`` CLI.
   -  Make use of ``pipenv sync`` in installation process to be
      consistent with Invenio 3.1.

-  Documentation:

   -  Fix a wrong docker image in the INSTALL.rst file.
   -  Add an issue template to the GitHub repository.
   -  Change license from GPLv2 to AGPLv3.

-  Fixed issues:

   -  #87: Add a button to expand or shrink the number of facet items
      displayed.
   -  #89 : Implement a minimal JSON schema for harvested document but
      map all documents into the same index for searching. Add a boolean
      key to identify harvested documents to disable editing
      functionality.
   -  #263 : Take library closed days into account as computing the due
      date.
   -  #357 : Display the correct patron when checking in a requested
      item if the pickup location is equal to the check-in transaction
      location.
   -  #378 : Compute due date based on the transaction library opening
      hours and calendar.
   -  #384 : Restore default boolean operator OR for search engine
      query, but improve order of results (form most to less pertinent).
   -  #407 : Improve confirmation message after item deletion.
   -  #417 : Compute due date, beginning at the end of the transaction
      day.

v.0.2.3
-------

Fix empty array in the publishers field

This patch also fixes #367.

v.0.2.2
-------

Fix empty publisher in the publishers field array

This patch also fixes #367

v.0.2.1
-------

Fix empty publishers field

This patch fixes #367.

v.0.2.0
-------

Search and notifications

-  Release version number following the `Semantic
   Versioning <https://semver.org>`__ recommandations
-  Circulation:

   -  “Notification” resource added (schema, mappings)
   -  Notification parameters added to the “circulation policy” resource
      (number of days before due date, number of days after due date)
   -  Automatic creation of four types of notifications: recall,
      availability (request), due soon, overdue first reminder
   -  Celery task cron to create and send overdue and due soon
      notifications
   -  Notification dispatcher created in order to send notifications to
      the proper patron, in his preferred language, through the
      appropriate channel

-  Search:

   -  ElasticSearch template mechanism implemented
   -  Analyzers applying to resource fields configured
   -  Field boosting configured
   -  Query parser using the boosting configuration

-  Consortium:

   -  New role: system librarian
   -  System librarian is granted full rights within his or her
      organisation
   -  Librarian allowed to edit, add, delete librarians of his or her
      library only
   -  Librarian cannot edit, delete system librarians
   -  Librarian allowed to manage users of his own library only (when
      edition is not authorized, the buttons are not diplayed)
   -  The selector of affiliation library presents only the authorized
      libraries

-  Permissions:

   -  Permission factory improved
   -  Permission data added to the REST API:

      -  Links to actions (create, update, delete)
      -  Reasons why a permission is denied

-  Fixtures: fix ``dojson`` transformation to adapt to RDA changes in
   the RERO data source
-  Instance: upgrade ``invenio-records`` to version 1.2.1, in order to
   enable dedicated table for each resource
-  Code quality:

   -  Improved users fixtures for tests, with relevant roles

-  Fixed issues: #52, #217, #349

v.0.1.0a22
----------

Consolidation and consortium features

-  User interface:

   -  Web notification using bootstrap toast component
   -  Pickup location name replaced by pickup library name
   -  Pickup location name column removed from patron profile (checkouts
      tab)

-  Professional user interface:

   -  Patron type and library IDs replaced by names
   -  Improved opening hours editor and validation
   -  Optional description fields for item and patron type
   -  Improved exceptions (holidays) editor
   -  *Add item* shortcut button removed from the professional document
      result view
   -  Re-ordered professional menu categories and subcategories

-  Circulation:

   -  New due date after renewal computed from current date instead of
      current due date
   -  Renewal removed from list of actions if new due date is shorter
      than the current one
   -  Check-out of in-transit items enabled (under specific conditions)
   -  Renewal of requested items disabled
   -  Corrected item status after checking in a requested item

-  Consortium:

   -  Multiple organisations support added
   -  Fixture data contains two organisations
   -  REST API result lists filtered by organisation
   -  REST API access restricted by organisation (read, write, delete,
      update)
   -  Item generation rewritten to comply with the two organisation
      model (item type, location)
   -  Loan generation rewritten to comply whith the two organisation
      model (item type, patron type, circulation policy, location, … )
   -  Action button\ *s* on professional documents view disabled for
      items not belonging to the current logged in librarian
      organisation.

-  eBooks:

   -  Cantook platform harvesting using the API (provides richer data)
      instead of OAI-PMH
   -  Cantook JSON transformed to Invenio MARC21 JSON (dojson)
   -  Invenio MARC21 JSON tranformed to RERO ILS JSON (dojson)
   -  Cantook cover art displayed if available

-  Instance:

   -  RERO ILS upgraded to Invenio 3.1
   -  Error level logs sent to a RERO hosted Sentry service for
      monitoring purpose
   -  `RERO EBOOKS <https://github.com/rero/rero-ebooks/>`__ upgraded to
      Invenio 3.1 (webpack implemented)
   -  RERO EBOOKS `v0.1.0a1
      released <https://github.com/rero/rero-ebooks/releases/tag/v0.1.0a1>`__

-  Code quality:

   -  Increase test coverage to 89%
   -  Fix all missing docstrings
   -  Commit message template updated accordingly to `Invenio
      recommandations <https://github.com/inveniosoftware/invenio/blob/master/CONTRIBUTING.rst#commit-messages>`__

-  Fixed issues: #58, #38 #155, #222, #223, #224, #230, #231, #232,
   #235, #254

v.0.1.0a21
----------

-  User interface:

   -  Upgrade to twitter bootstrap 4.1.3 and fontawesome 4.7.
   -  Simplification and harmonization of the user interface (public and
      professional views).
   -  The menu moved from the sidebar to the header, with a improve
      responsive behaviour.
   -  Favicons added.
   -  The document type also displayed in the item detailed view.
   -  Fix subjects facets issue (mapping).
   -  Hide facet when it’s empty and remove date range facet.
   -  Professional views are now an angular application:

      -  Circulation ui, circulation settings, library edition, all
         editors.
      -  Library and circulation policies are custom editors, the others
         are build with the form options, JSON shema, through
         ``angular6-json-schema-form``.
      -  Search for resources (libraries, patron types, item types,
         circulation policies, documents, patrons).
      -  On the fly translation mechanism implemented for angular
         application.
      -  A new modal dialog added in the professional views for
         resources deletion.

   -  Circulation user interface compliant with ``invenio-circulation``
      and circulation policies mechanism.
   -  Public search view rewritten in angular6.
   -  Autocomplete for the search (document and persons) with direct
      links to authorities.
   -  Remove ``invenio-search-ui`` from the dependencies.
   -  Reorder professional menus in a modular structure that should make
      sense to the professional.

-  Editors:

   -  Selector menus in the editor is dynamically populated (ie. PID are
      replaced by actual names).
   -  Libraries editor: completely rewritten:

      -  Opening hours can be set, as long as holidays and exceptions.
      -  Fields are dynamically validated.

-  Links between resources:

   -  Use the JSON reference resolution (``$ref``) supported by
      ``invenio``, for MEF Persons authorities too (through api).
   -  All PID links are JSON reference.
   -  Many search and detailed view have been updated correspondingly.
   -  Library facets is now based on the library PID.

-  API:

   -  New ``replace`` function, different from ``update``.
   -  ``is_open`` function to determine if the library is open.
   -  Resolvers added, especially a global one.
   -  A global ``can_delete`` function added, to identify if a resource
      can be deleted or not, also for item types and patron types.

-  Circulation:

   -  Integration of ``invenio-circulation`` and refactoring of
      circulation apis.
   -  Circulation ui refactoring to make use of the
      ``invenio-circulation`` api and the ``$ref`` mechanism.
   -  Circulation policies can be added, edited in a custom angular
      form.
   -  Circulation policies taken into account for each circulation
      transactions and the display of the request button.

-  Fixtures:

   -  Libraries with opening hours, holidays and exceptions.
   -  Data importation has been updated after the ``$ref`` refactoring,
      especially for links between bibliographic records and MEF Persons
      authorites.

-  Tests:

   -  All tests are now compliant with ``invenio-pytest``.

-  MEF:

   -  Document brief and detailed view display MEF authorities as a
      link.
   -  MEF persons detailed view provides a list of document for which
      this person is an author.
   -  MEF persons detailed view data are dynamically fetch on the MEF
      server (`mef.test.rero.ch <https://mef.test.rero.ch>`__)
   -  At indexation, data of the MEF record is injected into the
      document index.
   -  Improve the mapping and indexation of MEF record, in order to
      display the Person’s name depending on the language interface.

-  Fixed issues: #37, #43, #48, #70, #126, #114, #137, #164, #215, #221,
   #234

v.0.1.a20
---------

⚠ This note lists the changes that occurred since the ``v0.1.0a18`` release, ie
including the ``v0.1.0a19`` release.

-  Refactoring:

   -  ``reroils-app``, ``reroils-data``, ``reroils-record-editor``
      modules merged together and renamed to ``rero-ils``.
   -  Module structure and script helpers updated using the new released
      version of ``invenio-cookie-cutter``.
   -  New installation process and contributing guidelines documented.
   -  In the consortial structure, member renamed to library.

-  Cataloging:

   -  New ``rero-ils`` resource for authorities (MEF records), yet only
      for persons.
   -  Authorities for persons harvested form the new
      `MEF <https://mef.test.rero.ch>`__ RERO service.

-  Interface:

   -  Document covers displayed, when available.
   -  Facets:

      -  Reordering of facets.
      -  Replace locations by libraries facet.
      -  Facets are foldable and extendable.
      -  New sources facet for the persons results page.

   -  Persons are searchable (only by logged in librarian yet).
   -  Two detailed views implemented for persons, displaying data
      sources.
   -  New administration sidebar menu.
   -  New sticky autohide header bar, with new menu.

-  Editor:

   -  Deletion of record is verified: when the record is linked to other
      resources, then the delete button is disabled and a message is
      provided.

-  Harvesting: added a parameter to limit the number of records to
   harvest by OAI-PMH or API.
-  Circulation:

   -  The librarian can define patron types.
   -  The librarian can define item types.
   -  The librarian can define circulation policies.

-  Issues closed: #71, #20, #53, #44, #94, #109, #103, #111, #127, #125.

v0.1.0a18
---------

-  eBooks records from external services are imported and synchronized;
   from the detailed view of these eBooks, the users can bounce through
   a link to the source.
-  The search has now AND as a default boolean.

v0.1.0a17
---------

-  Data: add document types (articles, books, journals, scores, sounds,
   videos).
-  Fix issues #46, #57, #59, #61, #66

v0.1.0a16
---------

-  Fix issues #9, #11, #42
-  Fix translations errors.
-  Add circulation statecharts (item and loan point of view).

v0.1.0a15
---------

The content of v.0.1.0a14, due to a deployment error.

v0.1.0a14
---------

-  Circulation:

   -  The circulation UI supports now routing.
   -  The table of the pending view is sortable.
   -  Messages are displayed to the librarians when requested items are
      checked in.
   -  Messages are displayed to the librarian when requests are
      validated (new status at desk, or in transit).
   -  When a request is validated, the related patron is notified by
      email.

-  Fixtures:

   -  There is only one organisation with three members (libraries). The
      example looks like a true small network of libraries.
   -  Some patrons have been added, with predefined circulation
      transactions. These transactions can be set in the
      ```reroils-data/data/circulation-transactions.json`` <https://github.com/rero/reroils-data/blob/master/data/circulation_transactions.json>`__
      file. This is especially useful for testing purpose.

-  Data:

   -  The librarians can access the item full view, which displays the
      related circulation transactions (loan and requests).
   -  The visitors and logged in patrons aren’t authorized to access the
      members (libraries), locations and patrons full views.

-  User experience:

   -  The web interface is enriched with links that enables the
      librarians to access more quickly to the needed information or
      functions.
   -  The availability information has been simplified with only two
      colors: green if it’s available, red when it’s not. When an item
      isn’t available, some additional information is displayed when
      relevant (ie. due date).

-  Issues fixed:

   -  https://github.com/rero/reroils-app/issues/11
   -  https://github.com/rero/reroils-app/issues/26
   -  https://github.com/rero/reroils-app/issues/27

v0.1.0a13
---------

-  User management:

   -  Librarians can create users and grant or revoke them roles.

      -  Users with no roles can:

         -  log in
         -  and search for documents.

      -  Users with the *patron* role can:

         -  access their profile,
         -  place requests
         -  and borrow items.

      -  Users with the *staff* role are authorized to:

         -  manage all resources (documents, items, organisations,
            members, locations, users):
         -  make use of the circulation module.

-  Data:

   -  Item and patron barcodes are validated at creation in order to
      assure that they are unique. This is required by the
      circulation-ui module.
   -  Member and location codes are also validated.

-  Search:

   -  The placeholder of search input in the header changes according to
      the search view (documents, organisations, users). In the future,
      this will be a selector menu.

-  Circulation:

   -  The ``reroils-circulation-ui`` enables the management of requests
      (on items for now).
   -  Additional item states have been added, such as *at desk* (the
      item is ready to be picked up at the loan office) and *in transit*
      (the item is being sent from one library to another).
   -  In the circulation module, logged in librarians have access to a
      second tab that displays the pending requests related to their
      library.
   -  Librarians can validate requests, meaning that the item has been
      retrieved from the shelf. The item state changes accordingly (*at
      desk* or *in transit*).
   -  In the *check in / check out* tab, the renewal action is now
      available.

v0.1.0a12
---------

-  Users management:

   -  Patrons fixtures have been extended with actual circulation
      transactions, such as check out and pending request, and
      authentication data. Therefore, these patrons are ready for
      testing actions.
   -  Logged-in patrons can display their profile including personal
      data, list of borrowed and pending documents.

-  Data:

   -  A global API for all resources (records) is now available (class
      ``IlsRecords`` and ``RecordWithElements``).
   -  Circulation transactions are logged into a postgres table,
      enabling loan history.
   -  Logged patrons can make requests on items, except if the item is
      missing or if the item is already requested/loaned by the patron.
   -  When a patron request an item, a pick up location must be selected
      in a drop down menu.
   -  Requested items are marked as such in the document detailed view
      (On loan requested or requested).
   -  If there’s several request on the same item, the logged-in patron
      can see its rank in the pending list.

-  Circulation:

   -  The ``reroils-circulation-ui`` enables:

      -  patron basic information display, with borrowed item and due
         dates,
      -  check out (already in v.0.1.0a11),
      -  in check out mode, default actions are guessed by the system,
         but can be modified by the librarian before validation,
      -  check-in,
      -  check-in missing item (when found again),
      -  patron basic information display, with borrowed item and due
         dates.

-  Documentation: the `public demo
   help <https://github.com/rero/reroils-app/releases/tag/v0.1.0a12>`__
   has been moved to the ``reroils-app`` GitHub wiki.

v0.1.0a11
---------

-  Users management:

   -  Now we have patron’s accounts, with some fixtures.
   -  There’s a view for patrons.
   -  Patrons can be searched.
   -  The ``librarian@rero.ch`` is able to create a patron’s account.
   -  The patron’s account is linked to a user’s account through the
      email.

-  Data:

   -  The ``reroils-data`` module has been rewrited to get separated
      submodules for each type of record (documents, items,
      organisations, members, locations, patrons).
   -  Institutions, libraries and locations are now organisations,
      members and locations.
   -  Links now exists between:

      -  organisations, members and locations,
      -  patrons and users,
      -  patrons and items when a patron borrowed an item,
      -  items and locations. Links between documents and items were
         already implemented.

   -  The ``librarian@rero.ch`` can, from the document detailed view,
      add items and linked them to:

      -  documents,
      -  locations.

   -  When an item is created or edited, the barecode is checked in
      order to assure uniqueness.
   -  All record types (document, item, organisation, member, location,
      patron) can be created, edited and deleted.

-  Circulation:

   -  Now there a specific view for circulation (`an angular
      application <https://github.com/rero/reroils-circulation-ui>`__.
   -  The ``librarian@rero.ch`` can use it to lend items to a patron.
   -  The same view should be used to realize checkins and manual
      renewals in the future (to be tested).

v0.1.0a10
---------

-  Project:

   -  Changes now commited directly on github.
   -  Minimal contribution information available.

-  Fixtures:

   -  Development version of the ``populate.sh`` script generates less
      items, for performance purpose.
   -  There’s also fixtures for institutions, libraries and locations.

-  Editor:

   -  The editor is now more generic and can be used for all types of
      documents (bibliographic records, institutions records).
   -  Institutions, libraries and locations can be created, edited and
      deleted by the librarian user.
   -  There’s a search view for the same types of documents.

-  Users management:

   -  Visitors are able to create a user account, confirm their email
      address, reset their password.

 rero-ils v0.1.0
---------------------

rero-ils v0.1.0 was released on TBD, 2017.

About
~~~~~

rero21 ils data module

*This is an experimental developer preview release.*

What's new
~~~~~~~~~~

- Initial public release.

Installation
~~~~~~~~~~~~

   $ pip install rero-ils==0.1.0

Documentation
~~~~~~~~~~~~~

   https://rero-ils.readthedocs.io/

Happy hacking and thanks for flying rero-ils.

| RERO ILS Development Team
|   Email: info@rero.ch
|   Gitter: https://gitter.im/rero/reroils
|   Twitter: https://twitter.com/rero_centrale
|   GitHub: https://github.com/rero/rero-ils
|   URL: https://ils.test.rero.ch
