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

:warning: This note lists the changes that occurred since the
``v0.1.0a18`` release, ie including the ``v0.1.0a19`` release.

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
