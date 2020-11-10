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

v0.14.0
-------

This release note includes the changes of the ``rero-ils-ui`` project
[`link`_] .

User interface
~~~~~~~~~~~~~~

-  Displays the qualifier, status and note of the identifier in the
   document detailed view.
-  Translates the identifier types.
-  Displays in the patron account history, both professional and public
   interface, the item on loans that are in transit to house.

Professional interface
^^^^^^^^^^^^^^^^^^^^^^

-  Displays the new item note categories (see the `metadata`_ section),
   with an icon to identify public note.
-  Orders the requests in the modal to edit the request queue on an item
   by creation date.
-  Updates the patron type detailed view to display the circulation
   restrictions (see `circulation`_ section).
-  Updates the message displayed to the librarian when a patron is
   blocked.
-  Adds counters on the patron account tabs title of the professional
   interface.
-  Limits the payment account to 2 decimals in the transaction payment
   form (fee tab of the patron account of the circulation module).

Circulation
~~~~~~~~~~~

-  Fixes the loan API to include the correct action name ``extend``
   instead of ``extend_loan`` when a loan is renewed.
-  Fixes the cancellation of a request when there are several requests
   on the item.
-  Sort loan API response by loan creation date.
-  Implements circulation restrictions:

   -  Adds a limit on the total number of checkouts. Once the limit is
      reached, checkouts for this patron is blocked.
   -  Adds a limit depending the total amount of fees for a patron.
   -  Adds a limit on the number of overdue items. The limit is set in
      the ``patron_type`` record. Once the limit is reached, the patron
      cannot check out any items.

-  Rewrites the blocked patron restrictions to adapt to the new
   implemented restrictions.
-  Hides circulation actions in the public interface, either in document
   detailed view or in the patron account when the patron cannot operate
   these actions. The *renew* button is always displayed, but disabled
   when the action is not possible and an explanation is added in a
   tooltip.
-  Fixes a bug when checking in ``on_shelf`` or ``in_transit`` item
   (with no loan) that did not receive the correct item status.
-  Removes the time from the due date of a checked out item on the
   document detailed view of the public interface.
-  Fixes a bug with paid fees. In the patron account of the circulation
   module (professional interface), some paid fees still appeared, due
   to arithmetic operation (10 - 9,54 = 0.460000000000085).
-  Displays the pickup location name instead of the location name in the
   *to pickup* tab of the circulation module.
-  Updates circulation HTML template after the ``v0.13.0`` release to
   fix Cypress tests.
-  Allows librarians to cancel requests on item with *at desk* status.
   The ``cancel_request`` permissions had to be updated. A flash message
   warns the librarian about the item status. The item detailed view is
   updated after the request cancellation.
-  Adapts the patron name link, in the circulation module, to the
   context: in the checkin mode, the link points to the patron account
   of the circulation module, but in the patron account of the
   circulation module, it points to the patron detailed view of the
   professional interface.
-  Adds the patron age to the patron birth date in the patron account of
   the circulation module, to quicker identify children.
-  Allows the librarians to sort the checked out item of the patron
   account of the professional interface.
-  Improves the patron search of the circulation module to allow
   searching by barcode or patron name. A warning is displayed if the
   system found more than one result. The first result is displayed in
   the circulation module.

Metadata
~~~~~~~~

-  Makes the ``cantons`` field conditional of the ``sz`` (Switzerland)
   value of the ``county`` field.
-  Adds the following note categories to the item JSON schema:

   -  *binding note*.
   -  *provenance note.*
   -  *patrimonial note*.
   -  *acquisition note*.

-  Renames the *public note* to *general note*.
-  Adds the ``enumerationAndChronology`` filed to all type of items
   (issue and others).
-  Sorts the contribution roles in the document editor (with
   ``selectWithSort`` form option).
-  Improves the email validation message in several resources JSON
   schema.
-  Renames person module into contribution module.
-  Makes the holdings `vendor` field optional. It should not be required.

Acquisitions
~~~~~~~~~~~~

-  Adds a complete list of serial pattern templates, that are the most
   used patterns. These templates are now available to all librarians of
   all organisations.
-  Allows to use the expected date of a serial issue in the serial
   pattern template. This leverage the setting of the enumeration and
   chronology of the issue.
-  Improves the serial pattern preview. The number of HTTP calls have
   been reduced.
-  Displays late and claimed serial issues in the professional interface
   and in the public interface.

User management
~~~~~~~~~~~~~~~

-  Allows users without email. When a user without email attempt to
   reset his or her password, a warning message propose to contact a
   librarian.
-  Allows the librarian to change a patron password, with a button in
   the patron information of the patron account of the circulation
   module. The patron editor can be opened directly from the circulation
   module.
-  Displays the patron role in the circulation module and in the patron
   detailed view.
-  Allows users to give a second email for notification only, thus
   allowing a child to give its parent email.
-  Fixes a subscription renewal issue preventing to add to patron a
   subscription when they already have a valid one.
-  Requires an email for a user with librarian or system librarian role
   in the user editor.
-  Sets a default expiration date value to now + 3 years.

Permissions
~~~~~~~~~~~

-  Grants to the system librarian all the librarian rights.

API
~~~

-  Adds a configuration option to sort the API response by the record
   creation date.
-  Optimizes the number of API calls when requesting permissions from
   the professional interface.
-  Adds an ``invenio-account`` API to change a user password.

Tests
~~~~~

-  Cypress tests:

   -  Adds tests for resource template and template usage.
   -  Adds tests for the collections.
   -  Adds template fixtures.
   -  Adds cookie preservation to keep authentication information
      between tests.
   -  Adds a ``goToMenu`` command to Cypress to ease navigating the
      application.
   -  Adds tests for login and logout.
   -  Uses API calls to login and logout.
   -  Replaces UI actions by API calls in order to speed up the tests.
   -  Replaces UI navigation by ``cy.visit`` when relevant.
   -  Adds a method to get the current date and hour in order to use it
      in the API requests.
   -  Adds a method to create a document and an item with API calls.

Instance
~~~~~~~~

-  Fixes ``poetry`` version to ``<1.1.0``.

Issues
~~~~~~

-  `#918`_: Identifier type are not translated in the document detailed
   view.
-  `#1220`_: A method to keep authentication information for Cypress
   tests is needed.
-  `#1231`_: Selector with multiple choice are not alphabetically
   sorted.
-  `#1256`_: After a renewal, the new due date is not displayed in the
   professional view.
-  `#1278`_: The tab titles of the patron account of the professional
   interface should display a count of the items of the list.
-  `#1281`_: *Fees* is not translated in the patron account of the
   professional interface.
-  `#1285`_: The *canton* selector, in the document editor, should
   appear only if *Switzerland* is selected in the *country* selector.
-  `#1293`_: It’s not possible to cancel a request on an item with the
   *at desk* status.
-  `#1300`_: Display the pickup location name instead of the location
   name in the circulation module.
-  `#1303`_: Cannot delete a request of an item with multiple requests.
-  `#1314`_: Requests in the modal to edit the request queue are not
   ordered by creation date.
-  `#1317`_: The patron subscription renewal task raise issues in
   Sentry, because the ``get_patrons_without_subscriptions`` has a bug.
-  `#1334`_: The `circulation action`_ ``CHECKIN_1_1_2`` does not work
   as expected.
-  `#1340`_: A system librarian without the librarian role doesn’t have
   all librarian rights, resulting in bugs.
-  `#1355`_: The authors should be displayed in the requests (pending
   and at desk) of the patron account of the professional interface.
-  `#1356`_: Rename the request status *ready* into *to pick up* in the
   patron account of the public interface.
-  `#1357`_: Display the *renew* button in the patron account of the
   public interface, even if the action is disabled, and add
   explanations in the tooltip.
-  `#1360`_: The loan in transit to house are not displayed in the
   patron history (professional and public interface).
-  `#1364`_: Search by patron name in the checkin/checkout form
   (circulation module).
-  `#1373`_: In the patron account of the professional interface, some
   paid fees still appear.
-  `#1378`_: In the checkin form of the circulation module, the patron
   information should contain a different link depending if the module
   is in checkin or checkout mode, and display the age of the patron to
   identify children quicker.
-  `#1381`_: Email without full domain name can be saved in the patron
   and vendor editor.
-  `#1382`_: In the patron editor (JSON schema), the description of the
   ``street`` field should not ask for a coma.
-  `#1385`_: Replace *patron barcode* by *patron number* label in the
   patron account of the public interface.
-  `#1386`_: Do not display the patron birth date in the upper part of
   the patron account of the public interface. Instead, display it in
   the personal data tab, below.
-  `#1398`_: In the document detailed view of the public interface, when
   an item is on loan, the due date should not display the ``datetime``.
-  `#1403`_: The qualifier, status and note of the identifier should be
   displayed in the document detailed view.

.. _link: https://github.com/rero/rero-ils-ui
.. _metadata: #metadata
.. _circulation: #circulation
.. _#918: https://github.com/rero/rero-ils/issues/918
.. _#1220: https://github.com/rero/rero-ils/issues/1220
.. _#1231: https://github.com/rero/rero-ils/issues/1231
.. _#1256: https://github.com/rero/rero-ils/issues/1256
.. _#1278: https://github.com/rero/rero-ils/issues/1278
.. _#1281: https://github.com/rero/rero-ils/issues/1281
.. _#1285: https://github.com/rero/rero-ils/issues/1285
.. _#1293: https://github.com/rero/rero-ils/issues/1293
.. _#1300: https://github.com/rero/rero-ils/issues/1300
.. _#1303: https://github.com/rero/rero-ils/issues/1303
.. _#1314: https://github.com/rero/rero-ils/issues/1314
.. _#1317: https://github.com/rero/rero-ils/issues/1317
.. _#1334: https://github.com/rero/rero-ils/issues/1334
.. _circulation action: https://github.com/rero/rero-ils/blob/dev/doc/circulation/actions.md#checkin-form
.. _#1340: https://github.com/rero/rero-ils/issues/1340
.. _#1355: https://github.com/rero/rero-ils/issues/1355
.. _#1356: https://github.com/rero/rero-ils/issues/1356
.. _#1357: https://github.com/rero/rero-ils/issues/1357
.. _#1360: https://github.com/rero/rero-ils/issues/1360
.. _#1364: https://github.com/rero/rero-ils/issues/1364
.. _#1373: https://github.com/rero/rero-ils/issues/1373
.. _#1378: https://github.com/rero/rero-ils/issues/1378
.. _#1381: https://github.com/rero/rero-ils/issues/1381
.. _#1382: https://github.com/rero/rero-ils/issues/1382
.. _#1385: https://github.com/rero/rero-ils/issues/1385
.. _#1386: https://github.com/rero/rero-ils/issues/1386
.. _#1398: https://github.com/rero/rero-ils/issues/1398
.. _#1403: https://github.com/rero/rero-ils/issues/1403

v0.13.1
-------

This release note includes the changes of the ``rero-ils-ui`` project
[`link`_].

User Interface
~~~~~~~~~~~~~~

-  Updates the help link of the homepage to the actual help instead of
   the old GitHub wiki page.

Circulation
~~~~~~~~~~~

-  Fixes ILL request form validation issues that prevents ILL requests to
   be saved, or that saves ILL requests with wrong data.
-  Fixes a bug that raises an internal server error when checking out an
   item with requests.

Metadata
~~~~~~~~

-  Restores default value for hidden field in the cataloguing editor.
-  Improves the method to hide field in the cataloguing editor.

Search
~~~~~~

-  Fixes the contribution facets with an internationalization (i18n)
   filter.

User management
~~~~~~~~~~~~~~~

-  Fixes an error in the user editor when the role `patron` is
   selected.

Documentation
~~~~~~~~~~~~~

-  Removes from the pull request template checklist the item related to
   the translations, as they are managed in a specific branch.

Test
~~~~

-  Forces the version of Node.js used by the GitHub actions tests.

Instance
~~~~~~~~

-  Upgrades ``lxml`` and ``cryptography`` dependencies for security
   reasons.
-  Upgrades ``formly`` to ``v0.5.10.5``.
-  Upgrades ``@rero/ng-core`` to ``v0.13.0``.

Issues
~~~~~~

-  `rero-ils#1119`_: Non required fields of the document editor
   should support default values.
-  `rero-ils#1277`_: The help link on the homepage is deprecated.

.. _link: https://github.com/rero/rero-ils-ui
.. _rero-ils#1119: https://github.com/rero/rero-ils/issues/1119
.. _rero-ils#1277: https://github.com/rero/rero-ils/issues/1277

v0.13.0
-------

This release note includes the changes of the ``rero-ils-ui`` project
[`link`_].

User interface
~~~~~~~~~~~~~~

-  Displays the `new collection resource`_ on the public and
   professional interface: brief views for the search results and the
   collection detailed view.
-  Adds a link to extend the search to the union catalog when a search
   within a specific organisation retrieves no results.

Public interface
^^^^^^^^^^^^^^^^

-  Fixes the ``can_request`` JINJA filter of the document detailed view
   template, because it prevents a self registered user to display this
   view, and raises an internal server error.
-  Adds the new “collection” resource public detailed view.
-  Moves the *help* submenu entry to the new *Tools* menu.
-  Adds a RERO ID menu entry in the user menu. The profile displays the
   patron account, its loans, requests, fees… and the RERO ID displays
   the user personnal data, its credentials.
-  Allows the user to sign in with the username or the email.

Professional interface
^^^^^^^^^^^^^^^^^^^^^^

-  Adds a new resource to allow the librarian and the system librarian
   to create templates for several resources such as document,
   holdings, item, patron. The template JSON has a non validated filed,
   labelled `data`, that contains the pre-validated data.
   A template can be private, thus available only to its
   creator, or public and available to all librarians of the related
   organisation. Only system librarians can create or edit public
   templates.
-  Adds a new menu entry in the *Admin* menu to access the template
   search list.
-  Allows to group menu entries in the menu blocks of the professional
   interface homepage.
-  Creates the template brief view (search results) and detailed view.
-  Removes the possibility to add a template from the brief view, as it
   has to be done from the relevant resource.
-  Adapts the document, item, holdings, patron routes in order to be
   able to load data from an existing template in the editor.
-  Adds a *use it* functionality through a ``canUse`` permission that
   allows the user to use a template.
-  Allows duplication of records from the record detailed view. This
   leverages the creation of a new record similar to an existing one.
-  Updates the *Switch library* button to be compatible with the `new
   angular application initialization`_.
-  Displays the holdings depending on the ``holding_type`` metadata from
   the holdings itself, and not on the parent document type.
-  Renames the *patrons* entry of the *User services* menu into *users*.

Circulation
~~~~~~~~~~~

-  Fixes the requesting patron last name and surname when a requested
   item is checked in.
-  Adds a new resource for ILL requests, with related permissions (API)
   and tests.
-  Displays the ILL requests in a new tab of the patron profile.
-  Adds a new form for ILL requests, available to the patron in
   the public interface. This form allows the patron to place a request
   for a document not available in the patron’s organisation, and to
   select the pickup library.
-  Improves the loan API performance to render the patron account
   (public and professional) quicker.
-  Improves the performance of the patron account information in the
   checkin-checkout: a first call is requested to get linked item pids
   and barcode, then for each barcode, a second call is done to get the
   item details.

Metadata
~~~~~~~~

-  Improves the regular expression used in the JSON schema to validate
   dates, in all relevant resources.
-  Create the new “collection” resource, to group items together.
-  Adds optional fields to holdings that are displayed on the document
   detailed view:

   -  ``enumerationAndChronology``.
   -  ``supplementaryContent``.
   -  ``index``.
   -  ``missing_issues``.
   -  ``notes``.

-  Removes conditionality of the 2nd call number depending on an
   existing 1st call number.
-  Extends availability of the 2nd call number to all holdings types.
-  Prevents deleted serial issues to be displayed on the public
   interface.
-  Harmonizes the use of JSON schema custom options to sort items of
   selects in the editor.

Data
~~~~

-  Adds template records fixtures.
-  Fixes ``import_users`` CLI to prevent storing pids in the
   ``patron_pid`` database table, because it results in issues when
   creating new users after the initial setup.
-  Removes the ``append`` argument from the ``import_users`` function.
-  Adds a username to the user fixtures.

Search
~~~~~~

-  Fixes ElasticSearch bulk indexing to improve performance of parallel
   indexing with MEF authority link creation.
-  Adds facets to the template search view, to filter results by
   resource type (document, holdings, item, patron) and visibility
   (public, private).
-  Improves ES mapping configuration for users to prevent that searching
   for patron by barcode retrieves multiple results, if the barcode
   contains dashes.
-  Updates the total results display to ElasticSearch ``7.9.0``.

User management
~~~~~~~~~~~~~~~

-  Moves the user personal data from the user resource (JSON of the user
   module) to the RERO ID profile (the user profile database).
-  Extends the user resource with the following fields for patron:

   -  Notes (displayed in the patron profile).
   -  Expiration date (displayed in the patron profile).
   -  Library affiliation.

-  Group the patron data of the user in a nested structure.
-  Adds a new Invenio account login view REST API.
-  Moves the link between the patron record and the user profile from
   the email to the id.
-  Synchronizes the patron record and RERO ID profile data in both
   directions.
-  Sets the default user password as the birth date.
-  Renames the patron API endpoints from ``patrons`` to ``rero_users``.
-  Adds a user web API to return the number of patrons given a username
   in order to ensure that usernames are unique.

Tests
~~~~~

-  Adds fixtures for a new organisation for testing purpose.
   Existing records, such as organisation, library, patron type, etc.,
   makes the writing process of Cypress tests much easier.
-  Adds a model of a Cypress test to ease further the creation of
   Cypress tests and to provide a list of good practices.
-  Replaces ``cy.wait()`` by timeouts or by waiting for aliases to
   harden Cypress tests robustness.
-  Tests with Cypress the `circulation scenario A`_.
-  Tests with Cypress the `circulation scenario B`_.
-  Moves from Travis CI to GitHub actions to improve the preformance of
   running tests at each pull request or merged commit.
-  Updates Cypress tests to the patron module refactoring (renamed
   ``users``).

Angular application (Professional interface, search)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

-  Initializes the application according to Angular standards.

Instance
~~~~~~~~

-  Updates Cypress to ``v4.12.1``.
-  Updates ElasticSearch to ``7.9.0``.
-  Updates Invenio to ``3.3``.
-  Updates Celery to ``5.0.0``
-  Improves ElasticSearch monitoring by fixing ElasticSearch duplicate
   records computation.
-  Fixes an issue that prevented the Celery configuration fixture to be
   found by setting the constraint on the celery python package version
   (``<5.0.0``).
-  Fixes ``LXML`` errors during deployment. See `this Invenio pull
   request`_.
-  Enables ``invenio-admin`` and ``invenio-userprofiles``.
-  Adds an API to display the database connection counts. It allows to
   monitor the DB usage and to have statistics in order to decide how to
   improve the performance of a deployed instance.

Issues
~~~~~~

-  `rero-ils#83`_: Types are deprecated in ElasticSearch, then
   ``document_type`` parameter should not be used anymore. Fixed by
   upgrading Invenio to ``3.3``.
-  `rero-ils#1187`_: Date validation in JSON schema (editor) are not
   robust as it allows date such as 2020-67-74.
-  `rero-ils#1230`_: The requesting patron last and first name are
   inverted in circulation module interface when a requested item is
   checked in.
-  `rero-ils#1246`_: Displaying the patron account, either on the public
   or on the Professional interface is too slow, because the API
   response is not optimized.
-  `rero-ils#1252`_: Holdings for journals have several issues: hidden
   issues (items) cannot be expanded; the *description* tab is empty;
   receiving an issue is not possible when the holdings is imported from
   the legacy system (Virtua) with the wrong type (*standard* instead of
   *serial*); sometimes the library is not displayed in the holdings
   (only the location)…
-  `rero-ils#1264`_: A note is hardcoded in the courtesy notice
   (circulation notification). It should be removed from all
   notification templates.
-  `rero-ils#1284`_: Call numbers (1st and 2nd) should not have
   validation constraints, such as minimal number of characters.
-  `rero-ils#1272`_: As a logged patron displays his or her patron
   account, if a fee is on dispute, the view crashes and displays an
   internal server error.

.. _``rero-ils-ui``: https://github.com/rero/rero-ils-ui
.. _new collection resource: #metadata
.. _new angular application initialization: #angular-application-professional-interface-search
.. _circulation scenario A: https://github.com/rero/rero-ils/blob/dev/doc/circulation/scenarios.md#scenario_a-standard-loan
.. _circulation scenario B: https://github.com/rero/rero-ils/blob/dev/doc/circulation/scenarios.md#scenario_b-standard-loan-with-transit
.. _this Invenio pull request: https://github.com/inveniosoftware/cookiecutter-invenio-rdm/pull/88
.. _rero-ils#83: https://github.com/rero/rero-ils/issues/83
.. _rero-ils#1187: https://github.com/rero/rero-ils/issues/1187
.. _rero-ils#1230: https://github.com/rero/rero-ils/issues/1230
.. _rero-ils#1246: https://github.com/rero/rero-ils/issues/1246
.. _rero-ils#1252: https://github.com/rero/rero-ils/issues/1252
.. _rero-ils#1264: https://github.com/rero/rero-ils/issues/1264
.. _rero-ils#1284: https://github.com/rero/rero-ils/issues/1284
.. _rero-ils#1272: https://github.com/rero/rero-ils/issues/1272

v0.12.0
-------

This release note includes the changes of the ``rero-ils-ui`` project
[`link`_].

User interface
~~~~~~~~~~~~~~

-  Replaces the legacy ``authors`` by ``contribution`` filed in the
   search results view (brief view), detailed view and the loan
   transaction history of the public and professional interface. In the same
   move, the search input in the document editor, that allows to link a
   document to an authority record, is adapted to the new field (see below, in
   the `metadata`_ section).

Public interface
^^^^^^^^^^^^^^^^

-  Adds a tab for the fees in the patron account view.
-  Updates the entry menu link to the help page, to be consistent with
   the structure of the help section (``help/public``).

Professional interface
^^^^^^^^^^^^^^^^^^^^^^

-  Circulation interface:

   -  Adapts the circulation module interface after updating
      ``invenio-circulation`` and refactoring the RERO ILS circulation
      module (see below the `circulation`_ section).
   -  Fixes the renewal badge to prevent it to be displayed when an item
      that has been renewed is checked in.
   -  Replaces the pickup location name by the item’s library name of
      the item details.
   -  Adds an alert message to inform the librarian of the destination of a
      checked in item that goes in transit.
   -  Fixes the checkout view to allow removing the displayed patron
      information in order to switch to the checkin view. Removes a
      wrong flash error message that appears in such a move.
   -  Allows requests by a librarian in the name of a patron on all the
      organisation items, not on the library items only.

-  Document editor:

   -  Updates the document detailed view to display the
      ``new_acquisition`` field (see below, in the `metadata`_ section,
      the description of the *new acquisition* functionality).
   -  Fills the document editor with the data of a record imported
      through an external client using the REST API. As the librarian
      saves the record, the ``_draft`` boolean field is set to false to
      allow its validation (see below, in the `API`_ section).

Search
~~~~~~

-  Adapts the author facet to the new ``contribution`` field of the
   metadata model.
-  Fixes the total result count of the public search interface of an
   organisation view that is broken by the new ``contribution`` field
   implementation.

Circulation
~~~~~~~~~~~

-  Upgrades ``invenio-circulation`` from ``v1.0.0a16`` to ``v1.0.0a21``,
   then to ``v1.0.0a23``, ``v1.0.0a25``, ``v1.0.0a26``.
-  Fixes automatic item assignment on pending loans, preventing a
   checked-in item to be assigned to all pending loans of its document,
   by adding the ``assign_item`` parameter to all ``ITEM_RETURNED``
   transitions. Fixes `inveniosoftware/invenio-circulation#127`_.
-  Uses ``datetime`` to manage start and end date fields of the loans in
   ``rero-ils``, since ``invenio-circulation`` ``v1.0.0a21`` uses
   ``date`` format.
-  Implements `circulation actions`_, after an effort to extensively model all
   circulation use cases, for library network complex workflows:

   -  ``add_requests`` actions. Fixes issues when multiple requests are
      allowed for the same patron on the same item, and when loans with
      state ``ITEM_IN_TRANSIT_TO_HOUSE`` were blocking new requests.
   -  ``checkin`` actions.
   -  ``validate`` request actions. Fixes the issue when a manual
      validation of a request validates all requests on the same items.
   -  ``extend`` actions. Fixes an issue that allowed extension of a
      checked out item even if pending loans (requests) were associated
      to it.
   -  ``cancel_request`` actions.
   -  ``change_pickup_location`` actions.

-  Adds a ``LoanState`` class to better handle loan states.
-  Creates a ``item_record_to_a_specific_loan_state`` method to change
   the item record status.
-  Adds a configuration named ``CIRCULATION_LOAN_LOCATIONS_VALIDATIONS``
   to extend validation of loan locations (integrated to
   ``invenio-circulation`` ``v1.0.0a25``).
-  Fixes issues raising when placing several requests simultaneously
   (``invenio-circulation`` ``v1.0.0a26``).
-  Extends circulation fixtures to reflect improvements in the circulation
   module.
-  Allows an item having loans attached in ``CREATED`` state to be deleted.
   Such loans have no impact on circulation, as they are the result of
   interrupted circulation actions.
-  Fixes an issue preventing an item to be checked out if two pending loans
   (requests) are attached to it.
-  Allows circulation actions to be linked either to a transaction
   location or to a transaction library.
-  Renames the ``validate`` API call to ``validate_request``.
-  Fixes an issue occurring when multiple requests are being validated
   simultaneously.
-  Adds missing parameters to the renew button in the patron profile of
   the public interface.
-  Uses the loan field ``_created`` instead of ``transaction.date`` to
   sort requests. ``request_creation_date`` is equal to ``_created``.
-  Allows requests to be placed on ``ITEM_IN_TRANSIT_TO_HOUSE`` loans.
-  Adds item destination library name and code, and item destination
   location name and code to the loan dump to improve the circulation
   interface accuracy.
-  Fixes an issue that prevents the pickup location of a request of
   ``ITEM_IN_TRANSIT_TO_PICKUP`` loans to be changed.
-  Fixes an issue that prevents ``ITEM_IN_TRANSIT_TO_HOUSE`` loan to be checked
   out to a patron that does not own that loan.
-  Rewrites the loan permission factory and adds a specific class for
   ``invenio-circulation`` resource. Simplifies the ``search_factory``
   method. Fixes an error in the loan ``search_factory`` method when the
   user has both ``patron`` and ``librarian`` roles.
-  Implements the patron information in the ``invenio-sip2`` module`_, allowing
   patrons to access their information through the selfcheck machine: checked
   out items, requests, overdues, fees…

Metadata
~~~~~~~~

-  Improves ``marc2json`` and ``validate`` CLI commands to work properly
   with JSON references.
-  Moves a field of the document JSON schema that was badly situated
   after the splitting of the schema, from
   ``rero_ils/jsonschemas/common/languages.v0.0.1.json`` to
   ``rero_ils/modules/documents/jsonschemas/documents/document_series-v0.0.1.json``.
-  Implements the new ``contribution`` field (that replaces of the ``authors``
   field).
-  Replaces, in the document JSON schema, the labels of the agent roles
   by their code (ie, the content of the value key), in order to avoid
   translating the code and the label.
-  Adds a functionality in the *Reports & monitoring* section that
   allows a professional to export an item inventory list to a ``CSV``
   file. Before the creation of the export file, items can be
   filtered by library, location, item type and item status. The search
   itself retrieves items based on all their fields, such as the
   barcode or call number. That points to the list presented as a search
   result on RERO ILS.
-  Improves ``marc21tojson`` transformations with a better
   identification of empty values, and their replacement with default
   values.
- Allows (temporarily) to attach a serial holdings or a standard holdings to a
  document of journal type or periodical issuance type. This is necessary for
  migrating all the legacy system records to RERO ILS.

Acquisition
~~~~~~~~~~~

-  Updates the document and item JSON schemas for the new acquisition
   list management. These lists are generated through an ES query that
   filters the newly acquired items with a specific time span. This
   allows a librarian to define a permalink to be shared through the
   library website (or elsewhere), that points to a RERO ILS search
   result presenting the list.
-  Adds a search input in the order line editor to find a specific
   document and to save the librarian the burden of typing the full REST
   API document URL.

API
~~~

-  Adds ``marcxml`` support to the document API, thus allowing an
   authenticated user to post ``marcxml`` records using an external
   script. The record is added to the database with the ``_draft`` flag
   set to true, to disable the validation of the data and to avoid the
   record to be found in the catalog.

Permission
~~~~~~~~~~

-  Adds the ``document_importer`` role to users posting records
   (documents) through the REST API. A new CLI command creates a
   personal OAuth token for authentication.
-  Adds a method to return a record class from a given ``pid_type``.
   This method is available globally.

Tests
~~~~~

-  Adds fixture data for end to end (e2e) tests with `Cypress`_.
-  Splits ``commands.js`` `file`_ into multiple files to improve its
   readability and adds circulation custom commands to it.
-  Tests the creation of a simple document (required fields only).
-  Adds HTML ``id=""`` or ``name=""`` attributes in public and
   professional interfaces to ease the writing of the `Cypress`_ tests.
-  Fixes the item status of newly created items by copying an existing
   item through a function, with the existing status. This function,
   obviously, is only used for circulation unit tests, not for the
   regular item creation.
-  Adapts existing circulation unit tests to the new `circulation
   actions`_.
-  Extends circulation unit tests to cover all `circulation actions`_.
-  Adds circulation unit tests to cover all `circulation scenarios`_.

Scripts
~~~~~~~

-  Adds a script, called ``russian_dolls`` to package ``ng-core``,
   include it in ``rero-ils-ui``, and then package ``rero-ils-ui`` and
   include it in ``rero-ils``, to ease some development processes.

Instance
~~~~~~~~

-  Upgrades python dependencies after upgrading ``invenio-circulation``:
   removes constraints on ``marshmallow``, adds ``ciso8601``, fixes
   ``isort`` errors.
-  Fixes python imports after upgrading ``isort`` to ``v5``.
-  Fixes ``autoflake`` errors, signaling unused python imports.
-  Upgrades ``ngx-formly`` (the library that generates the editors,
   based on the JSON schemas) to ``5.9.1``.

Fixed issues
~~~~~~~~~~~~

-  `#797`_: The renewal badges appears in the circulation interface when
   a renewed item is checked in.
-  `#927`_: As a librarian, I cannot request (the request button is not
   displayed) an item that do not belongs to my library.
-  `#1030`_: In the document detailed view of the professional
   interface, the contributors that aren’t a link to an authority record
   (MEF link), but only a plain string, aren’t displayed.
-  `#1085`_: Item search by barcode is not filtered by organisation,
   resulting in possible circulation actions in the wrong organisation.
-  `#1137`_: The patron account view, in the public interface, crashes
   when an item of the loan transaction history is deleted.
-  `#1158`_: A missing configuration prevented the Celery scheduler to
   locate the ``task_clear_and_renew_subscriptions`` method.
-  `#1160`_: Checking out an item ready at desk to the patron that
   requested it is impossible. The error is “This item is requested by
   another patron”.

.. _link: https://github.com/rero/rero-ils-ui
.. _metadata: #metadata
.. _circulation: #circulation
.. _API: #api
.. _inveniosoftware/invenio-circulation#127: https://github.com/inveniosoftware/invenio-circulation/issues/127
.. _circulation actions: https://github.com/rero/rero-ils/blob/dev/doc/circulation/actions.md
.. _``invenio-sip2`` module: https://github.com/inveniosoftware-contrib/invenio-sip2
.. _Cypress: https://www.cypress.io/
.. _file: https://github.com/rero/rero-ils/tree/dev/tests/e2e/cypress/cypress/support
.. _circulation scenarios: https://github.com/rero/rero-ils/blob/dev/doc/circulation/scenarios.md
.. _#797: https://github.com/rero/rero-ils/issues/797
.. _#927: https://github.com/rero/rero-ils/issues/927
.. _#1030: https://github.com/rero/rero-ils/issues/1030
.. _#1085: https://github.com/rero/rero-ils/issues/1085
.. _#1137: https://github.com/rero/rero-ils/issues/1137
.. _#1158: https://github.com/rero/rero-ils/issues/1158
.. _#1160: https://github.com/rero/rero-ils/issues/1160g

v0.11.0
-------

User interface
--------------

-  Updates schema of forms to use the new sorted select menu.
-  Displays new metadata fields: ``seriesStatement`` and ``partOf``:

   -  Displays fields in detailed view and in editor.
   -  Removes ``partOf`` field from brief view.
   -  Adds ``oneOf`` attribute in order to link issuance ``maintype``
      and ``subtype`` in editor.

-  Adds missing translations of item notes types.
-  Limits length of document title to 150 characters in detailed view.
   Adds a *Show more*/*Show less* link if the title is truncated.
-  Sorts pickup locations alphabetically when placing a request for an
   item.

Professional interface
~~~~~~~~~~~~~~~~~~~~~~

-  Adds inventory list functionality and view based on ``item``
   resources. The librarian can access them using the ``Reports & Monitoring`` menu.
   This functionality allows the librarian to display a list of
   items, search and filter them and extract them to a CSV file for
   inventory purposes.

   -  Adds ``CSVSerializer`` to render list results to CSV.

-  Adds several improvements to the editor layout:

   -  Improves document ``JSONSchema`` form options by adding css
      classes, default values and form options to increase its
      usability.
   -  Adds borders to form groups and generally improves UI.
   -  Fixes fields to be displayed by default in editor, input sizes,
      always-hidden fields.

-  Adds a custom directive allowing to order tabs.
-  Changes the sequence of editor initialization to avoid concurrency
   problem with ``JSONSchema`` loading in BNF import editor.

Metadata
--------

-  Adds three new fields to the data model: ``seriesStatement``,
   ``partOf`` and ``issuance``.

   -  Implements transformation of these fields for ``MARC21`` and
      ``UNIMARC``.
   -  Adapts ES mappings and JSON schemas.
   -  Indexes host document title in child document’s record for search
      results relevance.

-  Adds a ``second_call_number`` field to ``item`` resource.
-  Splits document ``JSONSchema`` into smaller files, to improve
   readability. JSON references are resolved on the fly.

API
---

-  Refactors the permission processes using a permission factory and
   classes for specific resources instead of all resources.

   -  Refactors permission factories for resources: organisation,
      document, item, vendor.

Documentation
-------------

-  Documents the new ``Weblate`` translation workflow.

   -  Adds a Weblate badge in the ``README.rst`` that informs about the
      completion of translations, and points to the Weblate service.
   -  Removes the check of translation message extraction in the PR
      template.

-  Improves the ``rero-ils-ui`` README and adds badges as well as
   UCLouvain in copyright declaration.

Tests
-----

-  Adds an ``id`` on all menus in order to simplify and improve Cypress
   tests.

   -  Replaces ``getId()`` by ``idAttribute`` pipe from Angular.
   -  Doesn’t hide the Debug toolbar in Cypress tests as ``FLASK_DEBUG``
      should be set to ``False`` when launching the server.
   -  Creates new ``setLanguageToEnglish`` Cypress command to set
      language to English.
   -  Deletes all ``cy.visit()`` methods and use menus to navigate in the
      application.
   -  Creates new ``logout()`` Cypress command.
   -  Creates new ``goToMenu()`` Cypress command.
   -  Creates new ``createItem()`` Cypress command.
   -  Creates new ``goToItem()`` Cypress command.
   -  Improves ``checkout-checkin.spec.js`` Cypress tests using new
      Cypress commands.

-  Limits pytest version to <``6.0.0`` in order to avoid critical issues
   with newer versions.

Instance
--------

-  Upgrades ``node.js`` package from ``v10`` to ``v12``.
-  Updates ``poetry`` packages to latest versions.
-  Prepares the project for migration from `Transifex`_ to `Weblate`_
   translation web service. Pulls the translations from Transifex,
   extract messages and updates catalog.
-  Adds ``ngx-spinner`` dependency used in ``ng-core`` to
   ``rero-ils-ui``. ``ngx-spinner`` is used in version ``v8.1.0`` for
   compatibility with Angular 8.
-  The module ``rero-ils-ui`` uses the ``ng-core`` library in version
   ``v0.6.0``

Scripts
~~~~~~~

-  Fixes ``npm`` asset utils installation at ``bootstrap``: adds error
   message when npm asset utils fails and uses –force option for npm
   asset utils installation.
-  Improves ``Celery`` script option for server launching: adds new
   ``-l`` or ``--loglevel`` server script option to change Celery log
   level and adds new ``-n`` or ``--no-worker`` server script option to
   disable Celery workers.
-  Improves ``check_license`` method to include Triple-Slash directives
   for ``.js`` files, avoids checking screenshots directory in Cypress,
   and adds a triple slash directive on 2 JS files (from Cypress).

Fixed issues
------------

-  `#880`_: Reduce size of title in document detailed view
-  `#882`_: Translations of actions realised in circulation UI
-  `#883`_: Improvement needed on the request information when doing a
   checkin
-  `#886`_: Clear the patron info on top of checkin form when quitting it
-  `#898`_: Autocomplete stays even after the results list is displayed
-  `#906`_: Saving a document with edition responsibility impossible
-  `#916`_: Translate content field "Language" in document detailed view
   of public interface
-  `#917`_: Document type “Other” not translated in document detailed
   view (public interface)
-  `#1003`_: editor : multiple provision activity lost when editing a
   document
-  `#1035`_: Editor: “jump to” not always working
-  `#1078`_: The tab order of the document detailed view (pro interface)
   should be: get / description
-  `#1102`_: Authors and issuance fields: organisation as author and
   subtype are not loaded correctly when editing a record with those fields

.. _Transifex: https://www.transifex.com/
.. _Weblate: https://weblate.org
.. _#880: https://github.com/rero/rero-ils/issues/880
.. _#882: https://github.com/rero/rero-ils/issues/882
.. _#883: https://github.com/rero/rero-ils/issues/883
.. _#886: https://github.com/rero/rero-ils/issues/886
.. _#898: https://github.com/rero/rero-ils/issues/898
.. _#906: https://github.com/rero/rero-ils/issues/906
.. _#916: https://github.com/rero/rero-ils/issues/916
.. _#917: https://github.com/rero/rero-ils/issues/917
.. _#1003: https://github.com/rero/rero-ils/issues/1003
.. _#1035: https://github.com/rero/rero-ils/issues/1035
.. _#1078: https://github.com/rero/rero-ils/issues/1078
.. _#1102: https://github.com/rero/rero-ils/issues/1102

v0.10.1
-------

The `f01ceffe
<https://github.com/rero/rero-ils/commit/f01ceffe398c97e713f13db6ef8978eaca5de5bb>`__
and `38c982c1
<https://github.com/rero/rero-ils/commit/38c982c1064e85b4cd0bd56fe224016eedfea63d>`__
commits for the *Import from BnF* functionality are missing in the ``v0.10.0``
release. This patch fix this oversight.

v0.10.0
-------

User interface
--------------

Public interface
~~~~~~~~~~~~~~~~

-  Keeps the active tab on the document or person detailed view on page
   reloads.

Professional interface
~~~~~~~~~~~~~~~~~~~~~~

-  Renders the language menu with the same look as in the public
   interface:

   -  Uses the same icons.
   -  Removes the current language.
   -  Avoids to translate the language menu.
   -  Adds a divider to separate the language menu from the help link.

-  Takes the entire screen width. This is useful for the improvement of
   the editor.
-  Improves the document editor:

   -  Sets a max width for selects and inputs.
   -  Sets bold font weight for titles.
   -  Hides fields with unique value (as ``bf:Place``).
   -  Displays fields inline and makes this configurable through a HTML class
      in the JSON schema.
   -  Adds HTML class in the JSON schema to fix max width and title font
      size.

-  Implements interface components to import bibliographic records from
   external sources through the web (SRU protocol). The librarian searches in a
   regular search interface for the desired record, using a simple query
   (keywords for the author, title, date, IDs…), selects a record, gets a
   preview in two formats (the RERO ILS JSON rendered in HTML, and MARC). Once
   the desired record is identified, through an *Import* button, the record is
   loaded into the document editor to be modified and then added to the
   catalog. At this stage, only the BnF SRU service is implemented.
-  Fixes the redirection to the parent document after the deletion of an item.
   This behaviour has been generalized to every parent/child resource
   relationship through a modification in the routing configuration.
-  Allows to receive a serial issue through the professional
   interface (see the acquisition section, below). The workflow begins on the
   holding detailed view and then continues on a dedicated view for serial
   issues. The *Quick receipt* automatically receive a regular issue and create
   the corresponding item.
-  Improves the transaction data displayed on the item detailed view,
   depending on the transaction type (checkout or request), to avoid
   displaying an empty pickup location name when this data is not
   relevant.

Circulation
-----------

-  Adapts the patron profile URL in notification messages to the active RERO
   ILS instance.
-  Adds a CLI for notifications to start the notification process with
   ``invenio run notifications process``.

Metadata
--------

-  Adds a translation mechanism for the resource editor (documents, items…).
   The translated schemas keys in the `rero-ils` project are served through an
   API endpoint to the `rero-ils-ui` project, in order to avoid translating
   them twice.
-  Holding record, serial pattern:

   -  Adds a field to describe the publication frequency of a serial pattern.
      The librarian has to pick from a fixed list of 15 frequencies, which
      correspond to the standard RDA list.
   -  Adds an ``expected_date_for_first_issue`` field to indicate the expected
      date of the first issue to be received.
   -  Sets the ``next_expected_date`` field as required for regular
      frequencies.
   -  Adapts the item JSON schema to display fields conditionally.

-  Adds ``type`` field in the item record, to distinguish between
   standard item and serial issue. If the item is of type ``issue``,
   then the ``issue`` field is required, to describe the issuance
   details and issue status. Issue items can only be attached to
   holdings of serial type.
   The field ``item_type`` that indicates the circulation category will
   be removed later. The item circulation status is described in the
   ``item.status`` field, while the issue status is described in the
   ``item.issue.status``.
-  Adds ``notes`` field in the item JSON schema. Four types of notes have been
   added, two regarding their audience (public or staff) and two regarding a
   circulation operation (checkin/checkout). The notes are displayed according
   to their type: public notes are publicly displayed on the document detail
   view of the public interface, staff notes are displayed on the same view but
   in the professional interface, checkin notes are displayed as a permanent
   alert as the item is checked in, and checkout notes are displayed as a
   circulation transaction occurs.
-  Uses ``JSONSCHEMAS_REPLACE_REFS = True`` to resolve JSON reference
   before serving the schema.
-  Removes the ``document-minimal-v0.0.1.json`` schema, as it is not
   used.

Acquisition
-----------

-  Receive an issue:

   -  Allows the librarian to receive new issues through the holdings detailed
      view. The system, based on the holdings pattern, computes the next issue
      pattern and expected date. The librarian is able to add irregular or
      exceptional issues.
   -  Updates automatically the ``next_expected_date`` after a successful
      receipt of a regular issue (``expected_date`` of the receipt issue plus
      the pattern frequency).

API
---

-  Corrects the process used when starting a delayed bulk indexing
   (switch from ``invenio-indexer`` to ``IlsRecordindexer``).
-  Uses the standard JSON schema end point (``/schemas``).
-  Restricts the receipt of issue to librarians of the  holdings record's
   library.
-  The pattern preview API returns the ``issue_display_text`` (based on
   the preview template) and the ``expected_date``.
-  The holding API is able to receive the next regular issue.

Documentation
-------------

-  Documents all circulation actions, trying to be the most
   comprehensive in the context of a library network with complex internal
   circulation workflows. Actions, scenarios and chart can be found in
   ```/doc/README.md#circulation``
   <https://github.com/rero/rero-ils/blob/dev/doc/README.md#circulation>`__. In
   the same move, the babel configuration has been cleaned.
-  Removes unnecessary documentation in the ``LICENSE`` file.
-  Fixes the ``AUTHORS.rst`` file (wrong indentation).
-  Improves the github issue templates to automatically add various labels to
   the issue, depending on the type of issue (bug, correction, enhancement,
   etc.). This should also ease the process of issue creation and triage.
-  Creates an API to expose which roles can be managed by the current
   logged user. Introduces a restriction to prevent the current user to
   delete itself.

Translation
-----------

-  Fixes a wrong rule in the babel configuration that prevented strings
   to be extracted from the document JSON schema.

Instance
--------

-  Upgrades assets utilities (``clean-css``, ``node-sass``\ …)
-  Fixes version number in the ``pyproject.toml`` file.
-  Uses enabled state of tasks already saved in REDIS.
-  Integrates ``invenio-sip2`` module, that can be installed with a new
   option for the ``bootstrap`` script.
-  The module ``rero-ils-ui`` uses the ``ng-core`` library in version
   ``v0.5.0``.

Scripts
~~~~~~~

-  Fixes ``server`` script to make use of the correct scheduler backend
   and prevents ``rero_ils.schedulers.RedisScheduler`` file creation.

Fixed issues
------------

-  `#802 <https://github.com/rero/rero-ils/issues/802>`__: In the
   notification sent to the patron, the patron profile URL isn’t adapted
   to the running RERO ILS instance URL.
-  `#821 <https://github.com/rero/rero-ils/issues/821>`__: The switch
   library menu of the professional interface should be better positioned. The
   menu itself should directly inform the librarian of which library is
   selected. Furthermore, the switch library menu should be displayed on every
   page of the professional interface, not only on the home page. When another
   library is selected, the page is reloaded with the new context, implying a
   possible data loss.
-  `#822 <https://github.com/rero/rero-ils/issues/822>`__: The switch
   library menu of the professional interface is not dynamically
   populated after the creation of a new library.
-  `#930 <https://github.com/rero/rero-ils/issues/930>`__: A librarian
   could edit librarian records of other libraries and manage system
   librarian roles.
-  `#943 <https://github.com/rero/rero-ils/issues/943>`__: Selecting
   another interface language in the professional interface wasn’t
   changing the language of the editor.
-  `#1033 <https://github.com/rero/rero-ils/issues/1033>`__: Restarting
   the scheduler disables entries.
-  `#1036 <https://github.com/rero/rero-ils/issues/1036>`__: ``notes``
   field prevents to save document record.
-  `#1038 <https://github.com/rero/rero-ils/issues/1038>`__: The person
   selector in the document editor doesn’t display the birth and death dates of
   the person correctly.

Known issues
------------

There are some critical issues on the editor, that are known and are
going to be fixed by one of the next sprints (July 2020 or August 2020):

-  `#906 <https://github.com/rero/rero-ils/issues/906>`__: saving a document
   with edition responsibility is not possible.
-  `#1003 <https://github.com/rero/rero-ils/issues/1003>`__: multiple provision
   activity are lost when editing a document.
-  `#1035 <https://github.com/rero/rero-ils/issues/1035>`__: the navigation
   helper (*jump to*) is not always functioning.


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
