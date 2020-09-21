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

Changes
=======

`v0.12.0 <https://github.com/rero/rero-ils/tree/v0.12.0>`__ (2020-09-21)
------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.12.0rc...v0.12.0>`__

**Implemented enhancements:**

-  Switch to professional interface at login
   `#933 <https://github.com/rero/rero-ils/issues/933>`__

**Fixed bugs:**

-  A wrong message appears on the document detailed view of the
   professional interface
   `#1223 <https://github.com/rero/rero-ils/issues/1223>`__
-  The BnF import is wrong for provision activity.
   `#1219 <https://github.com/rero/rero-ils/issues/1219>`__
-  State of button on/off in circulation policy editor
   `#891 <https://github.com/rero/rero-ils/issues/891>`__

**Closed issues:**

-  Network protection and “any later version” removed from license
   `#1186 <https://github.com/rero/rero-ils/issues/1186>`__
-  Removing existing restriction on available pickup location prevents
   to save the record
   `#988 <https://github.com/rero/rero-ils/issues/988>`__
-  Check that all buttons (from UI) follow the circulation policy
   `#936 <https://github.com/rero/rero-ils/issues/936>`__
-  Translations of roles in patron editor
   `#881 <https://github.com/rero/rero-ils/issues/881>`__
-  No action is performed in checkin form
   `#831 <https://github.com/rero/rero-ils/issues/831>`__
-  Checked in item from other library doesn’t go in transit
   `#813 <https://github.com/rero/rero-ils/issues/813>`__
-  Checkin of item on shelf, with request to validate
   `#801 <https://github.com/rero/rero-ils/issues/801>`__
-  Checkin on item on shelf from other library
   `#800 <https://github.com/rero/rero-ils/issues/800>`__

**Merged pull requests:**

-  translations: translate for release v0.12.0
   `#1234 <https://github.com/rero/rero-ils/pull/1234>`__
   (`jma <https://github.com/jma>`__)
-  patron: fix profile translations
   `#1229 <https://github.com/rero/rero-ils/pull/1229>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  dojson: fix unimarc publishers provision activity
   `#1224 <https://github.com/rero/rero-ils/pull/1224>`__
   (`rerowep <https://github.com/rerowep>`__)

`v0.12.0rc <https://github.com/rero/rero-ils/tree/v0.12.0rc>`__ (2020-09-14)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.11.0...v0.12.0rc>`__

**Implemented enhancements:**

-  The help menu should point to the public help page if clicked from
   public interface
   `#1127 <https://github.com/rero/rero-ils/issues/1127>`__
-  scripts: install ng-core and ui in main project
   `#1142 <https://github.com/rero/rero-ils/pull/1142>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  cypress: enhance Cypress commands precision
   `#1136 <https://github.com/rero/rero-ils/pull/1136>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  tests: enhance Cypress with fixtures
   `#1125 <https://github.com/rero/rero-ils/pull/1125>`__
   (`blankoworld <https://github.com/blankoworld>`__)

**Fixed bugs:**

-  message ‘prêt impossible’ : l’exemplaire est demandé par un autre
   lecteur `#1160 <https://github.com/rero/rero-ils/issues/1160>`__
-  celery scheduler can not locate the method
   task_clear_and_renew_subscriptions
   `#1158 <https://github.com/rero/rero-ils/issues/1158>`__
-  Selects aren’t alphabetically sorted when the form options have the
   code as value of the ``label`` and ``value`` keys
   `#1149 <https://github.com/rero/rero-ils/issues/1149>`__
-  Public patron profile view raises an error 500
   `#1145 <https://github.com/rero/rero-ils/issues/1145>`__
-  Patron profile view raises an error 410 (error 500 displayed) when an
   item of the history is deleted
   `#1137 <https://github.com/rero/rero-ils/issues/1137>`__
-  The circulation interface mixes item barcodes between organisations.
   `#1085 <https://github.com/rero/rero-ils/issues/1085>`__
-  Contributors without MEF links not displayed in pro detailed view
   `#1030 <https://github.com/rero/rero-ils/issues/1030>`__
-  documents: import EAN - some abstracts are HTML encoded
   `#743 <https://github.com/rero/rero-ils/issues/743>`__
-  test: fix autoflake errors
   `#1176 <https://github.com/rero/rero-ils/pull/1176>`__
   (`rerowep <https://github.com/rerowep>`__)

**Closed issues:**

-  The property numbering_script is either in the wrong file, or to be
   deleted `#1147 <https://github.com/rero/rero-ils/issues/1147>`__
-  Impossible to request a document of another library
   `#927 <https://github.com/rero/rero-ils/issues/927>`__
-  Renewal badge irrelevant for checked in items
   `#797 <https://github.com/rero/rero-ils/issues/797>`__
-  UI : Replace RXJS “combineLatest”
   `#549 <https://github.com/rero/rero-ils/issues/549>`__

**Merged pull requests:**

-  release: v0.12.0rc
   `#1210 <https://github.com/rero/rero-ils/pull/1210>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  persons: fix public search count
   `#1205 <https://github.com/rero/rero-ils/pull/1205>`__
   (`rerowep <https://github.com/rerowep>`__)
-  holdings: allow creating std holdings on journal
   `#1197 <https://github.com/rero/rero-ils/pull/1197>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  search: remove useless translated facets
   `#1195 <https://github.com/rero/rero-ils/pull/1195>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  document: replace role label content with values
   `#1194 <https://github.com/rero/rero-ils/pull/1194>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  editor: fix error 400 when saving a simple document
   `#1192 <https://github.com/rero/rero-ils/pull/1192>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  package: update dependencies
   `#1191 <https://github.com/rero/rero-ils/pull/1191>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  US1546 marcxml support
   `#1189 <https://github.com/rero/rero-ils/pull/1189>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  acquisition: add document selector for order lines
   `#1185 <https://github.com/rero/rero-ils/pull/1185>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  utils: new method to return record class
   `#1183 <https://github.com/rero/rero-ils/pull/1183>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation: fix validate request return type
   `#1177 <https://github.com/rero/rero-ils/pull/1177>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  circulation: fix change pickup location on loans
   `#1174 <https://github.com/rero/rero-ils/pull/1174>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  help: update the public help menu entry url
   `#1172 <https://github.com/rero/rero-ils/pull/1172>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  Translations update from Weblate
   `#1171 <https://github.com/rero/rero-ils/pull/1171>`__
   (`weblate <https://github.com/weblate>`__)
-  permission: refactoring the loan permission factory
   `#1170 <https://github.com/rero/rero-ils/pull/1170>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  circulation: allow requests on ITEM_IN_TRANSIT_TO_HOUSE loans.
   `#1169 <https://github.com/rero/rero-ils/pull/1169>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  US1394 invenio circulation
   `#1166 <https://github.com/rero/rero-ils/pull/1166>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  inventory: export document creator field
   `#1163 <https://github.com/rero/rero-ils/pull/1163>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  wiki: update the public help menu entry url
   `#1162 <https://github.com/rero/rero-ils/pull/1162>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  patron: fix missing configuration for patron subscriptions
   `#1159 <https://github.com/rero/rero-ils/pull/1159>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  data: reorganisation of json schema.
   `#1156 <https://github.com/rero/rero-ils/pull/1156>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Translations update from Weblate
   `#1154 <https://github.com/rero/rero-ils/pull/1154>`__
   (`weblate <https://github.com/weblate>`__)
-  Translations update from Weblate
   `#1153 <https://github.com/rero/rero-ils/pull/1153>`__
   (`weblate <https://github.com/weblate>`__)
-  patron profile: fix for plural translation
   `#1148 <https://github.com/rero/rero-ils/pull/1148>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  cypress: split commands.js in several files
   `#1143 <https://github.com/rero/rero-ils/pull/1143>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  Translations update from Weblate
   `#1141 <https://github.com/rero/rero-ils/pull/1141>`__
   (`weblate <https://github.com/weblate>`__)
-  patron: no history returned for deleted items
   `#1139 <https://github.com/rero/rero-ils/pull/1139>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Translations update from Weblate
   `#1138 <https://github.com/rero/rero-ils/pull/1138>`__
   (`weblate <https://github.com/weblate>`__)
-  marc21tojson: fix transformation errors
   `#1134 <https://github.com/rero/rero-ils/pull/1134>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Translations update from Weblate
   `#1131 <https://github.com/rero/rero-ils/pull/1131>`__
   (`weblate <https://github.com/weblate>`__)
-  item: update item/doc for new acquisition
   `#1130 <https://github.com/rero/rero-ils/pull/1130>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  data model: implement contribution
   `#1129 <https://github.com/rero/rero-ils/pull/1129>`__
   (`rerowep <https://github.com/rerowep>`__)
-  patron account: add fees tab
   `#1124 <https://github.com/rero/rero-ils/pull/1124>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  cli: marc21json cli function to use splitted json schemas
   `#1120 <https://github.com/rero/rero-ils/pull/1120>`__
   (`rerowep <https://github.com/rerowep>`__)
-  cypress: test the creation of a simple document
   `#1116 <https://github.com/rero/rero-ils/pull/1116>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  SIP2: implement patron information
   `#1096 <https://github.com/rero/rero-ils/pull/1096>`__
   (`lauren-d <https://github.com/lauren-d>`__)

`v0.11.0 <https://github.com/rero/rero-ils/tree/v0.11.0>`__ (2020-08-03)
------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.10.1...v0.11.0>`__

**Implemented enhancements:**

-  Reduce size of title in document detailed view
   `#880 <https://github.com/rero/rero-ils/issues/880>`__
-  server: enable options to server script
   `#1115 <https://github.com/rero/rero-ils/pull/1115>`__
   (`blankoworld <https://github.com/blankoworld>`__)

**Fixed bugs:**

-  Authors and issuance fields: organisation as author and subtype are
   not loaded correctly when editing a record with those fields
   `#1102 <https://github.com/rero/rero-ils/issues/1102>`__
-  Autocomplete stays even after the results list is displayed
   `#898 <https://github.com/rero/rero-ils/issues/898>`__

**Closed issues:**

-  The tab order of the document detailed view (pro interface) should
   be: get / description
   `#1078 <https://github.com/rero/rero-ils/issues/1078>`__
-  editor : multiple provision activity lost when editing a document
   `#1003 <https://github.com/rero/rero-ils/issues/1003>`__
-  Document type “Other” not translated in document detailed view
   (public interface)
   `#917 <https://github.com/rero/rero-ils/issues/917>`__
-  Translate content field “Language” in document detailed view of
   public interface
   `#916 <https://github.com/rero/rero-ils/issues/916>`__
-  Saving a document with edition responsibility impossible
   `#906 <https://github.com/rero/rero-ils/issues/906>`__
-  Clear the patron info on top of checkin form when quitting it
   `#886 <https://github.com/rero/rero-ils/issues/886>`__
-  Improvement needed on the request information when doing a checkin
   `#883 <https://github.com/rero/rero-ils/issues/883>`__
-  Translations of actions realised in circulation UI
   `#882 <https://github.com/rero/rero-ils/issues/882>`__

**Merged pull requests:**

-  pytest: fix deprecation warnings on version 6.0.0
   `#1121 <https://github.com/rero/rero-ils/pull/1121>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  documents: improve editor layout
   `#1118 <https://github.com/rero/rero-ils/pull/1118>`__
   (`jma <https://github.com/jma>`__)
-  Us1491 item inventory list
   `#1114 <https://github.com/rero/rero-ils/pull/1114>`__
   (`jma <https://github.com/jma>`__)
-  permission: refactoring acquisition resources permission factory
   `#1113 <https://github.com/rero/rero-ils/pull/1113>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  permission: refactoring resources permission factory
   `#1110 <https://github.com/rero/rero-ils/pull/1110>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  documentation: fix README weblate badge
   `#1109 <https://github.com/rero/rero-ils/pull/1109>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  deployment: node 12
   `#1108 <https://github.com/rero/rero-ils/pull/1108>`__
   (`rerowep <https://github.com/rerowep>`__)
-  documentation: add a weblate badge to the README
   `#1106 <https://github.com/rero/rero-ils/pull/1106>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  cypress: enhance commands to improve tests
   `#1104 <https://github.com/rero/rero-ils/pull/1104>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  permission: refactoring document permission factory
   `#1103 <https://github.com/rero/rero-ils/pull/1103>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  ui: select menu items by Cypress through ids
   `#1101 <https://github.com/rero/rero-ils/pull/1101>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  check_license: accept Triple Slash Directive
   `#1098 <https://github.com/rero/rero-ils/pull/1098>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  translations: prepare project for weblate
   `#1092 <https://github.com/rero/rero-ils/pull/1092>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  request: sort alphabetically pickup location
   `#1090 <https://github.com/rero/rero-ils/pull/1090>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  bootstrap scripts: fix npm utils installation
   `#1088 <https://github.com/rero/rero-ils/pull/1088>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  poetry: update packages to their last version
   `#1087 <https://github.com/rero/rero-ils/pull/1087>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  json schema: use the select menu with order
   `#1086 <https://github.com/rero/rero-ils/pull/1086>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  document: translate document type in detail view
   `#1083 <https://github.com/rero/rero-ils/pull/1083>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  editor: fix edition statement saving problem.
   `#1071 <https://github.com/rero/rero-ils/pull/1071>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  branch for the data model series user story
   `#1069 <https://github.com/rero/rero-ils/pull/1069>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  schema: split JSON schemas
   `#1056 <https://github.com/rero/rero-ils/pull/1056>`__
   (`rerowep <https://github.com/rerowep>`__)
-  permissions: refactoring organisation permissions
   `#1051 <https://github.com/rero/rero-ils/pull/1051>`__
   (`zannkukai <https://github.com/zannkukai>`__)

`v0.10.1 <https://github.com/rero/rero-ils/tree/v0.10.1>`__ (2020-07-02)
------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.10.0...v0.10.1>`__

**Merged pull requests:**

-  US1274: Import from BnF
   `#1076 <https://github.com/rero/rero-ils/pull/1076>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)

`v0.10.0 <https://github.com/rero/rero-ils/tree/v0.10.0>`__ (2020-07-01)
------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.9.1...v0.10.0>`__

**Implemented enhancements:**

-  Improvement needed on the switch library menu
   `#821 <https://github.com/rero/rero-ils/issues/821>`__

**Fixed bugs:**

-  Editor: “jump to” not always working
   `#1035 <https://github.com/rero/rero-ils/issues/1035>`__
-  Delete disabled button doesn’t allow to show reasons not to delete
   `#945 <https://github.com/rero/rero-ils/issues/945>`__
-  The switch library menu is not dynamically populated
   `#822 <https://github.com/rero/rero-ils/issues/822>`__

**Closed issues:**

-  A librarian can change his/her affiliation library in the editor
   `#1039 <https://github.com/rero/rero-ils/issues/1039>`__
-  Author search in document creation display wrong date.
   `#1038 <https://github.com/rero/rero-ils/issues/1038>`__
-  Impossible to save the document editor with field “notes”
   `#1036 <https://github.com/rero/rero-ils/issues/1036>`__
-  Restarting scheduler is disabling entries
   `#1033 <https://github.com/rero/rero-ils/issues/1033>`__
-  Redirection after item deletion from the item detailed view
   `#1024 <https://github.com/rero/rero-ils/issues/1024>`__
-  Librarian permissions are too large on other librarian records
   `#930 <https://github.com/rero/rero-ils/issues/930>`__
-  Language switch does not work properly on the professional interface
   `#925 <https://github.com/rero/rero-ils/issues/925>`__
-  Bigger thumbnails in public view
   `#903 <https://github.com/rero/rero-ils/issues/903>`__
-  Link to the patron profile not adapted to the concerned instance in
   the notification message.
   `#802 <https://github.com/rero/rero-ils/issues/802>`__
-  Barcode and callnumber (at item level) shoudn’t be mandatory
   `#648 <https://github.com/rero/rero-ils/issues/648>`__

**Merged pull requests:**

-  translations: fetch new translations
   `#1072 <https://github.com/rero/rero-ils/pull/1072>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  documentation: add an issue template for dev
   `#1064 <https://github.com/rero/rero-ils/pull/1064>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  document: fix edition with notes
   `#1062 <https://github.com/rero/rero-ils/pull/1062>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  Merge US1275 on dev
   `#1060 <https://github.com/rero/rero-ils/pull/1060>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  Zan us1351 items notes
   `#1057 <https://github.com/rero/rero-ils/pull/1057>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  translation: fix string extraction from JSON file
   `#1054 <https://github.com/rero/rero-ils/pull/1054>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  authorization: create role management API
   `#1043 <https://github.com/rero/rero-ils/pull/1043>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  cli: correct wrong process bulk queue
   `#1037 <https://github.com/rero/rero-ils/pull/1037>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  scheduler: use saved enabled state of tasks
   `#1034 <https://github.com/rero/rero-ils/pull/1034>`__
   (`rerowep <https://github.com/rerowep>`__)
-  license: update missing info in the license
   `#1031 <https://github.com/rero/rero-ils/pull/1031>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  notifications: patron url
   `#1029 <https://github.com/rero/rero-ils/pull/1029>`__
   (`rerowep <https://github.com/rerowep>`__)
-  ui: keep selected tab active on reload
   `#1025 <https://github.com/rero/rero-ils/pull/1025>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  docs: add the missing references to the add_request circulation
   action. `#1023 <https://github.com/rero/rero-ils/pull/1023>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  translations: adds editor translations support
   `#1021 <https://github.com/rero/rero-ils/pull/1021>`__
   (`jma <https://github.com/jma>`__)
-  scripts: correct server script
   `#1015 <https://github.com/rero/rero-ils/pull/1015>`__
   (`rerowep <https://github.com/rerowep>`__)
-  merge US1296 to dev (UX of editor)
   `#1012 <https://github.com/rero/rero-ils/pull/1012>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  install: integration of invenio-sip2 module
   `#1005 <https://github.com/rero/rero-ils/pull/1005>`__
   (`lauren-d <https://github.com/lauren-d>`__)

`v0.9.1 <https://github.com/rero/rero-ils/tree/v0.9.1>`__ (2020-06-03)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.9.0...v0.9.1>`__

**Closed issues:**

-  Action realised in circulation must be in the past participle
   `#890 <https://github.com/rero/rero-ils/issues/890>`__

**Merged pull requests:**

-  Documentation resources: circulation actions, reroils_resources and
   loan state chart
   `#1017 <https://github.com/rero/rero-ils/pull/1017>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  translation: fix translations API
   `#1013 <https://github.com/rero/rero-ils/pull/1013>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  nginx logging `#1007 <https://github.com/rero/rero-ils/pull/1007>`__
   (`rerowep <https://github.com/rerowep>`__)


`v0.9.0 <https://github.com/rero/rero-ils/tree/v0.9.0>`__ (2020-06-02)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.8.0...v0.9.0>`__

**Implemented enhancements:**

-  Workflow when seizing opening hours
   `#675 <https://github.com/rero/rero-ils/issues/675>`__
-  An informative README is missing!
   `#627 <https://github.com/rero/rero-ils/issues/627>`__
-  Language facet behaviour (number of results)
   `#91 <https://github.com/rero/rero-ils/issues/91>`__

**Fixed bugs:**

-  Errors when running run_tests.sh
   `#1000 <https://github.com/rero/rero-ils/issues/1000>`__
-  Persons can be indexed twice resulting in duplicate records
   `#834 <https://github.com/rero/rero-ils/issues/834>`__

**Closed issues:**

-  Permissions for item/patron types and circ policies
   `#932 <https://github.com/rero/rero-ils/issues/932>`__
-  Cancel button in patron profile
   `#929 <https://github.com/rero/rero-ils/issues/929>`__
-  Focus not set in many views
   `#928 <https://github.com/rero/rero-ils/issues/928>`__
-  Suppress the item detailed view of the public interface
   `#884 <https://github.com/rero/rero-ils/issues/884>`__
-  Delay for display selector content for item types at item creation
   `#819 <https://github.com/rero/rero-ils/issues/819>`__
-  search: problem with brackets [ ] in the query
   `#755 <https://github.com/rero/rero-ils/issues/755>`__

**Merged pull requests:**

-  document: delete link to item detail view
   `#1011 <https://github.com/rero/rero-ils/pull/1011>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  test: fix run-test and setup
   `#1001 <https://github.com/rero/rero-ils/pull/1001>`__
   (`rerowep <https://github.com/rerowep>`__)
-  v0.9.0 translations
   `#998 <https://github.com/rero/rero-ils/pull/998>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  translations: add translations API
   `#997 <https://github.com/rero/rero-ils/pull/997>`__
   (`jma <https://github.com/jma>`__)
-  persons: link persons to source instead of MEF
   `#996 <https://github.com/rero/rero-ils/pull/996>`__
   (`rerowep <https://github.com/rerowep>`__)
-  documentation: add an actual README to the project
   `#995 <https://github.com/rero/rero-ils/pull/995>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  project: fix keyboard interruption for scripts
   `#994 <https://github.com/rero/rero-ils/pull/994>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  setup: fix old pipenv environment variables
   `#992 <https://github.com/rero/rero-ils/pull/992>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  patrons: check if a patron email is unique
   `#990 <https://github.com/rero/rero-ils/pull/990>`__
   (`jma <https://github.com/jma>`__)
-  schemas: fix patron transaction events schema
   `#987 <https://github.com/rero/rero-ils/pull/987>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  dependencies: use poetry
   `#986 <https://github.com/rero/rero-ils/pull/986>`__
   (`jma <https://github.com/jma>`__)
-  Permissions : Refactoring permissions usage
   `#985 <https://github.com/rero/rero-ils/pull/985>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  ebooks: fix holdings update when importing ebooks
   `#984 <https://github.com/rero/rero-ils/pull/984>`__
   (`rerowep <https://github.com/rerowep>`__)
-  tests: fix travis trouble with pytest-invenio
   `#981 <https://github.com/rero/rero-ils/pull/981>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  US1305 data model illustrations colors physical details
   `#980 <https://github.com/rero/rero-ils/pull/980>`__
   (`rerowep <https://github.com/rerowep>`__)
-  tests: fix units testing for generated item barcodes
   `#979 <https://github.com/rero/rero-ils/pull/979>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  tests: fix travis
   `#977 <https://github.com/rero/rero-ils/pull/977>`__
   (`rerowep <https://github.com/rerowep>`__)
-  location: unique pickup location for a library
   `#976 <https://github.com/rero/rero-ils/pull/976>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  celery: redis scheduler backend
   `#974 <https://github.com/rero/rero-ils/pull/974>`__
   (`rerowep <https://github.com/rerowep>`__)
-  rest api: add simple query support
   `#973 <https://github.com/rero/rero-ils/pull/973>`__
   (`jma <https://github.com/jma>`__)
-  item: field call number is now optional
   `#971 <https://github.com/rero/rero-ils/pull/971>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  document: suppress item detail view
   `#970 <https://github.com/rero/rero-ils/pull/970>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  item: multiple inheritance for the item class
   `#968 <https://github.com/rero/rero-ils/pull/968>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  db: separate tables
   `#959 <https://github.com/rero/rero-ils/pull/959>`__
   (`rerowep <https://github.com/rerowep>`__)
-  enqueues notifications
   `#951 <https://github.com/rero/rero-ils/pull/951>`__
   (`rerowep <https://github.com/rerowep>`__)
-  patron: add blocking functionnality
   `#902 <https://github.com/rero/rero-ils/pull/902>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  tests: implement first tests with cypress
   `#878 <https://github.com/rero/rero-ils/pull/878>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  data: update JSON schema to draft 07
   `#862 <https://github.com/rero/rero-ils/pull/862>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  api: test existence of pid’s
   `#853 <https://github.com/rero/rero-ils/pull/853>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Paging (stack request) functionnalities
   `#708 <https://github.com/rero/rero-ils/pull/708>`__
   (`zannkukai <https://github.com/zannkukai>`__)

`v0.8.0 <https://github.com/rero/rero-ils/tree/v0.8.0>`__ (2020-05-04)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.7.0...v0.8.0>`__

**Fixed bugs:**

-  persons does not appears in the autocomplete search input
   `#964 <https://github.com/rero/rero-ils/issues/964>`__
-  pickup location is not updated in item detail view using Chrome
   `#960 <https://github.com/rero/rero-ils/issues/960>`__
-  Briew view display bug when quickly clicking from tab to tab
   `#901 <https://github.com/rero/rero-ils/issues/901>`__
-  Autocomplete results not displayed, click in the input needed
   `#788 <https://github.com/rero/rero-ils/issues/788>`__
-  Changes of communication language for patrons are effective but not
   displayed `#583 <https://github.com/rero/rero-ils/issues/583>`__

**Closed issues:**

-  Initial Update `#923 <https://github.com/rero/rero-ils/issues/923>`__
-  document : staff can’t indicate an eISBN or an eISSN as identifier
   `#895 <https://github.com/rero/rero-ils/issues/895>`__
-  Location URI are not filtered by library for a system librarian
   `#697 <https://github.com/rero/rero-ils/issues/697>`__
-  display of qualifier for persons in RERO ILS
   `#657 <https://github.com/rero/rero-ils/issues/657>`__
-  Jean-Paul II (GND) not in MEF anymore
   `#555 <https://github.com/rero/rero-ils/issues/555>`__
-  Journal/giornale appears as “Città” in facet document type
   `#529 <https://github.com/rero/rero-ils/issues/529>`__

**Merged pull requests:**

-  documentation: add dependencies in PR template
   `#963 <https://github.com/rero/rero-ils/pull/963>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  permission: fix organisation permission
   `#957 <https://github.com/rero/rero-ils/pull/957>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  publication pattern: create a manual prediction
   `#952 <https://github.com/rero/rero-ils/pull/952>`__
   (`jma <https://github.com/jma>`__)
-  notification: use pickup location email as sender
   `#950 <https://github.com/rero/rero-ils/pull/950>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Us1293 doo invenio32
   `#949 <https://github.com/rero/rero-ils/pull/949>`__
   (`jma <https://github.com/jma>`__)
-  test: fix external ones
   `#946 <https://github.com/rero/rero-ils/pull/946>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  test: fix run-test
   `#942 <https://github.com/rero/rero-ils/pull/942>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Merge “Subscription” branch to dev
   `#940 <https://github.com/rero/rero-ils/pull/940>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  setup: fix ref. prob. on responsibilityStatement
   `#938 <https://github.com/rero/rero-ils/pull/938>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  loan: update request pickup location
   `#935 <https://github.com/rero/rero-ils/pull/935>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  notification: use responsibility statement
   `#926 <https://github.com/rero/rero-ils/pull/926>`__
   (`rerowep <https://github.com/rerowep>`__)
-  test: safety check
   `#924 <https://github.com/rero/rero-ils/pull/924>`__
   (`rerowep <https://github.com/rerowep>`__)
-  fault save ebook harvesting
   `#922 <https://github.com/rero/rero-ils/pull/922>`__
   (`rerowep <https://github.com/rerowep>`__)
-  location: add test to increase code coverage
   `#919 <https://github.com/rero/rero-ils/pull/919>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘it’
   `#912 <https://github.com/rero/rero-ils/pull/912>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  permissions: update permission API and configuration
   `#893 <https://github.com/rero/rero-ils/pull/893>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  document: adapt serializer to filter by org in admin view
   `#852 <https://github.com/rero/rero-ils/pull/852>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  persons: display idref persons
   `#845 <https://github.com/rero/rero-ils/pull/845>`__
   (`rerowep <https://github.com/rerowep>`__)

`v0.7.0 <https://github.com/rero/rero-ils/tree/v0.7.0>`__ (2020-04-09)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.6.1...v0.7.0>`__

**Implemented enhancements:**

-  Browsing during setup
   `#869 <https://github.com/rero/rero-ils/issues/869>`__

**Fixed bugs:**

-  Protect the library custom editor
   `#575 <https://github.com/rero/rero-ils/issues/575>`__

**Closed issues:**

-  Action menu for fees
   `#871 <https://github.com/rero/rero-ils/issues/871>`__
-  Not possible to create some of the loan fixtures
   `#838 <https://github.com/rero/rero-ils/issues/838>`__
-  Space after pickup location name
   `#830 <https://github.com/rero/rero-ils/issues/830>`__
-  Flash message for checkin with fees, requests or transit
   `#829 <https://github.com/rero/rero-ils/issues/829>`__
-  Alignment of checkins and checkouts infos
   `#827 <https://github.com/rero/rero-ils/issues/827>`__
-  Validation message “Record Created with pid”
   `#805 <https://github.com/rero/rero-ils/issues/805>`__
-  Focus set in the list of requests to validate
   `#803 <https://github.com/rero/rero-ils/issues/803>`__
-  Item detailed view: missing circulation info
   `#798 <https://github.com/rero/rero-ils/issues/798>`__
-  Patron to display in the checkin form
   `#793 <https://github.com/rero/rero-ils/issues/793>`__
-  Authorisations `#787 <https://github.com/rero/rero-ils/issues/787>`__
-  Location settings aren’t explained in the editor and an online pickup
   location is possible
   `#604 <https://github.com/rero/rero-ils/issues/604>`__

**Merged pull requests:**

-  ui: move to rero-ils-ui v0.1.0
   `#915 <https://github.com/rero/rero-ils/pull/915>`__
   (`jma <https://github.com/jma>`__)
-  location: correct schema to work well with formly
   `#914 <https://github.com/rero/rero-ils/pull/914>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  project: fix sqlalchemy last releases problems
   `#910 <https://github.com/rero/rero-ils/pull/910>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  translation: fix key source issues
   `#909 <https://github.com/rero/rero-ils/pull/909>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘en’
   `#908 <https://github.com/rero/rero-ils/pull/908>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘nl’
   `#904 <https://github.com/rero/rero-ils/pull/904>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘es’
   `#900 <https://github.com/rero/rero-ils/pull/900>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘it’
   `#897 <https://github.com/rero/rero-ils/pull/897>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  git: integrate US1232 into dev
   `#896 <https://github.com/rero/rero-ils/pull/896>`__
   (`reropag <https://github.com/reropag>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘ar’
   `#892 <https://github.com/rero/rero-ils/pull/892>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  fixture: recreation of documents for MEF
   `#889 <https://github.com/rero/rero-ils/pull/889>`__
   (`rerowep <https://github.com/rerowep>`__)
-  issues: trim item and patron barcodes
   `#887 <https://github.com/rero/rero-ils/pull/887>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  security: fix bleach ReDOS security breach
   `#872 <https://github.com/rero/rero-ils/pull/872>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  acquisition: cleanup useless functions of order lines resource
   `#867 <https://github.com/rero/rero-ils/pull/867>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  vulnerability: fix PyYaml CVE vulnerability
   `#866 <https://github.com/rero/rero-ils/pull/866>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  project: improve test on dates
   `#863 <https://github.com/rero/rero-ils/pull/863>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  test: fix library opening timezone due date
   `#859 <https://github.com/rero/rero-ils/pull/859>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  data: fix location data problem
   `#858 <https://github.com/rero/rero-ils/pull/858>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  bootstrap: fix useless tgz file installation
   `#857 <https://github.com/rero/rero-ils/pull/857>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  security: fix bleach XSS security breach
   `#854 <https://github.com/rero/rero-ils/pull/854>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  document: fix cover image in public detailed view
   `#848 <https://github.com/rero/rero-ils/pull/848>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  tests: fix Zürich timezone problems
   `#847 <https://github.com/rero/rero-ils/pull/847>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  db: fix sequence indentifier
   `#846 <https://github.com/rero/rero-ils/pull/846>`__
   (`rerowep <https://github.com/rerowep>`__)
-  request: fix request made by a librarian
   `#843 <https://github.com/rero/rero-ils/pull/843>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  location: adapt JSON schema for pickup_name required if is_pickup
   `#842 <https://github.com/rero/rero-ils/pull/842>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  installation: fix python packages dependencies
   `#841 <https://github.com/rero/rero-ils/pull/841>`__
   (`jma <https://github.com/jma>`__)
-  tests: fix dependencies and security check
   `#839 <https://github.com/rero/rero-ils/pull/839>`__
   (`jma <https://github.com/jma>`__)
-  tests: fix problems with daylight saving time
   `#836 <https://github.com/rero/rero-ils/pull/836>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  requests: place a request for a patron by a librarian
   `#835 <https://github.com/rero/rero-ils/pull/835>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  monitoring: monitoring for DB and ES
   `#833 <https://github.com/rero/rero-ils/pull/833>`__
   (`rerowep <https://github.com/rerowep>`__)
-  release: v0.6.1 `#825 <https://github.com/rero/rero-ils/pull/825>`__
   (`jma <https://github.com/jma>`__)
-  circulation: return all applied actions after a checkin or checkout
   `#824 <https://github.com/rero/rero-ils/pull/824>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Transform “Fees” to “PatronTransaction” data model
   `#820 <https://github.com/rero/rero-ils/pull/820>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  documentation: update INSTALL.rst
   `#818 <https://github.com/rero/rero-ils/pull/818>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  patron editor: add placeholders
   `#815 <https://github.com/rero/rero-ils/pull/815>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  public interface: improve patron request deletion
   `#808 <https://github.com/rero/rero-ils/pull/808>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  utils: $ref from pid
   `#765 <https://github.com/rero/rero-ils/pull/765>`__
   (`rerowep <https://github.com/rerowep>`__)
-  metadata: electronicLocator
   `#761 <https://github.com/rero/rero-ils/pull/761>`__
   (`rerowep <https://github.com/rerowep>`__)
-  documentation: Flask-Wiki integration
   `#740 <https://github.com/rero/rero-ils/pull/740>`__
   (`jma <https://github.com/jma>`__)
-  acquisition: create invoice resource
   `#729 <https://github.com/rero/rero-ils/pull/729>`__
   (`lauren-d <https://github.com/lauren-d>`__)

`v0.6.1 <https://github.com/rero/rero-ils/tree/v0.6.1>`__ (2020-03-02)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.6.0...v0.6.1>`__

**Closed issues:**

-  Adapt request to validate to the library switch
   `#817 <https://github.com/rero/rero-ils/issues/817>`__

**Merged pull requests:**

-  ui: move to rero-ils-ui 0.0.12
   `#823 <https://github.com/rero/rero-ils/pull/823>`__
   (`jma <https://github.com/jma>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘nl’
   `#814 <https://github.com/rero/rero-ils/pull/814>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  cli: fix typo `#811 <https://github.com/rero/rero-ils/pull/811>`__
   (`lauren-d <https://github.com/lauren-d>`__)

`v0.6.0 <https://github.com/rero/rero-ils/tree/v0.6.0>`__ (2020-02-26)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.5.2...v0.6.0>`__

**Implemented enhancements:**

-  Display Popup for a checkin operation if item are in transit
   `#783 <https://github.com/rero/rero-ils/issues/783>`__
-  Better menus `#483 <https://github.com/rero/rero-ils/issues/483>`__
-  Validation of Circulation policy settings
   `#213 <https://github.com/rero/rero-ils/issues/213>`__
-  global Provider
   `#106 <https://github.com/rero/rero-ils/issues/106>`__
-  print(e) `#86 <https://github.com/rero/rero-ils/issues/86>`__

**Fixed bugs:**

-  Irma is not able to open the circulation policy editor
   `#626 <https://github.com/rero/rero-ils/issues/626>`__
-  Circulation policy custom editor do not load patron types and item
   types settings `#625 <https://github.com/rero/rero-ils/issues/625>`__
-  Indexing : Deleting ‘mef_persons’ cause ‘index_not_found’ exception
   `#601 <https://github.com/rero/rero-ils/issues/601>`__
-  A librarian of organisation A is allowed to checkout an item of
   organisation B `#600 <https://github.com/rero/rero-ils/issues/600>`__
-  Suppression of a document: no confirmation
   `#552 <https://github.com/rero/rero-ils/issues/552>`__
-  Wrong organisation when adding item or patron types
   `#389 <https://github.com/rero/rero-ils/issues/389>`__
-  Authors facets does not appear on public search view
   `#372 <https://github.com/rero/rero-ils/issues/372>`__
-  Opening hours editor page has to be refreshed to display changes
   `#337 <https://github.com/rero/rero-ils/issues/337>`__
-  indexer: fix person indexing
   `#711 <https://github.com/rero/rero-ils/pull/711>`__
   (`rerowep <https://github.com/rerowep>`__)
-  tests: fix run-test
   `#702 <https://github.com/rero/rero-ils/pull/702>`__
   (`rerowep <https://github.com/rerowep>`__)

**Closed issues:**

-  Display of “No loan for the current patron”
   `#799 <https://github.com/rero/rero-ils/issues/799>`__
-  Display action realised in checkin form
   `#792 <https://github.com/rero/rero-ils/issues/792>`__
-  Message to be displayed as checking out an item requested by another
   patron `#791 <https://github.com/rero/rero-ils/issues/791>`__
-  Circulation UI: missing space between first and last name
   `#790 <https://github.com/rero/rero-ils/issues/790>`__
-  Circulation: trim barcode
   `#789 <https://github.com/rero/rero-ils/issues/789>`__
-  Short fixture correction Wang > Wang
   `#695 <https://github.com/rero/rero-ils/issues/695>`__
-  Facets order should be consistent through global and organisations
   views `#688 <https://github.com/rero/rero-ils/issues/688>`__
-  Flash messages should always start with a capitalized initial.
   `#661 <https://github.com/rero/rero-ils/issues/661>`__
-  missing mapping in JSON files
   `#649 <https://github.com/rero/rero-ils/issues/649>`__
-  Wrong french traduction of “System librarian” on the homepage of
   ils.test.rero.ch
   `#646 <https://github.com/rero/rero-ils/issues/646>`__
-  Item type with name “Standard”
   `#624 <https://github.com/rero/rero-ils/issues/624>`__
-  Add locations to other libraries
   `#622 <https://github.com/rero/rero-ils/issues/622>`__
-  Validation messages should be set in the form options
   `#605 <https://github.com/rero/rero-ils/issues/605>`__
-  Attaching an item to an harvested ebook should not be possible
   `#603 <https://github.com/rero/rero-ils/issues/603>`__
-  Due date according to opening hours not working
   `#599 <https://github.com/rero/rero-ils/issues/599>`__
-  New/edit patron required field validation
   `#584 <https://github.com/rero/rero-ils/issues/584>`__
-  Missing translations: patron editor
   `#572 <https://github.com/rero/rero-ils/issues/572>`__
-  Persons aren’t filtered by views
   `#550 <https://github.com/rero/rero-ils/issues/550>`__
-  Missing create button for the first record of a given resource
   `#541 <https://github.com/rero/rero-ils/issues/541>`__
-  Missing space between the check boxes and the titles of the roles in
   the patron registration form
   `#539 <https://github.com/rero/rero-ils/issues/539>`__
-  Search autocomplete in jinja detailed views.
   `#242 <https://github.com/rero/rero-ils/issues/242>`__
-  Checkin of item with requests: in transit to wrong library
   `#780 <https://github.com/rero/rero-ils/issues/780>`__
-  Select pickup locations instead of library name
   `#777 <https://github.com/rero/rero-ils/issues/777>`__
-  Library code displayed in the holding
   `#776 <https://github.com/rero/rero-ils/issues/776>`__
-  Requests to validate by library switching
   `#775 <https://github.com/rero/rero-ils/issues/775>`__
-  Wrong locations proposed in the item editor
   `#772 <https://github.com/rero/rero-ils/issues/772>`__
-  Impossible to create a user with role “librarian”
   `#771 <https://github.com/rero/rero-ils/issues/771>`__
-  In transit to: destination not displayed
   `#770 <https://github.com/rero/rero-ils/issues/770>`__
-  In transit to: display library name
   `#769 <https://github.com/rero/rero-ils/issues/769>`__

**Merged pull requests:**

-  ui: move to rero-ils-ui 0.0.11
   `#809 <https://github.com/rero/rero-ils/pull/809>`__
   (`jma <https://github.com/jma>`__)
-  isort: fix isort problems for two files
   `#807 <https://github.com/rero/rero-ils/pull/807>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘es’
   `#796 <https://github.com/rero/rero-ils/pull/796>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘ar’
   `#785 <https://github.com/rero/rero-ils/pull/785>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  data: correction on users data
   `#781 <https://github.com/rero/rero-ils/pull/781>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  items: fix automatic checkin return informations
   `#774 <https://github.com/rero/rero-ils/pull/774>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘de’
   `#763 <https://github.com/rero/rero-ils/pull/763>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  translation: fix error with translation file
   `#762 <https://github.com/rero/rero-ils/pull/762>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘es’
   `#759 <https://github.com/rero/rero-ils/pull/759>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘en’
   `#758 <https://github.com/rero/rero-ils/pull/758>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘fr’
   `#757 <https://github.com/rero/rero-ils/pull/757>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  public interface: request deletion by patron
   `#756 <https://github.com/rero/rero-ils/pull/756>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘es’
   `#750 <https://github.com/rero/rero-ils/pull/750>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  Translate ‘/rero_ils/translations/messages.pot’ in ‘en’
   `#748 <https://github.com/rero/rero-ils/pull/748>`__
   (`transifex-integration[bot] <https://github.com/apps/transifex-integration>`__)
-  tests: fix travis failed with werkzeug==1.0.0
   `#747 <https://github.com/rero/rero-ils/pull/747>`__
   (`jma <https://github.com/jma>`__)
-  documentation: complete authors page
   `#745 <https://github.com/rero/rero-ils/pull/745>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  acq_account: disable account deletion when it has orders linked to
   it. `#737 <https://github.com/rero/rero-ils/pull/737>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  loans: fix problem when api returns an invalid checkout loan period
   `#735 <https://github.com/rero/rero-ils/pull/735>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  improve bnf import
   `#733 <https://github.com/rero/rero-ils/pull/733>`__
   (`rerowep <https://github.com/rerowep>`__)
-  config: add default sort on resources
   `#731 <https://github.com/rero/rero-ils/pull/731>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  editor: fix “required status” error in item editor
   `#728 <https://github.com/rero/rero-ils/pull/728>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  item: add field location on form configuration
   `#727 <https://github.com/rero/rero-ils/pull/727>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  ui: Search input takes now all the header area
   `#724 <https://github.com/rero/rero-ils/pull/724>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  doc: create reroils resource diagram to show relations
   `#722 <https://github.com/rero/rero-ils/pull/722>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  data: preload persons and export
   `#721 <https://github.com/rero/rero-ils/pull/721>`__
   (`rerowep <https://github.com/rerowep>`__)
-  acquisition: link order line to a document
   `#719 <https://github.com/rero/rero-ils/pull/719>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  person: atomic persons creation and indexation
   `#715 <https://github.com/rero/rero-ils/pull/715>`__
   (`rerowep <https://github.com/rerowep>`__)
-  US813 `#714 <https://github.com/rero/rero-ils/pull/714>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Acquisition `#709 <https://github.com/rero/rero-ils/pull/709>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  ui: display a different logo/color for each orga.
   `#706 <https://github.com/rero/rero-ils/pull/706>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  ES: fix mapping `#705 <https://github.com/rero/rero-ils/pull/705>`__
   (`rerowep <https://github.com/rerowep>`__)
-  deployment: adaptions for rero-ils-ui
   `#700 <https://github.com/rero/rero-ils/pull/700>`__
   (`rerowep <https://github.com/rerowep>`__)
-  setup: speed up and clean improvements
   `#699 <https://github.com/rero/rero-ils/pull/699>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  script: add rero-ils-ui install from tgz
   `#692 <https://github.com/rero/rero-ils/pull/692>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  editor: move to ngx-formly
   `#690 <https://github.com/rero/rero-ils/pull/690>`__
   (`jma <https://github.com/jma>`__)
-  loans: improve due date timezone consideration
   `#684 <https://github.com/rero/rero-ils/pull/684>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  libraries: add sort by name configuration
   `#681 <https://github.com/rero/rero-ils/pull/681>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  cli: fixture pid dependency test with config file
   `#679 <https://github.com/rero/rero-ils/pull/679>`__
   (`rerowep <https://github.com/rerowep>`__)
-  scripts: fix objects indexation
   `#678 <https://github.com/rero/rero-ils/pull/678>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  person: filter by view …
   `#676 <https://github.com/rero/rero-ils/pull/676>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  filter persons view
   `#674 <https://github.com/rero/rero-ils/pull/674>`__
   (`rerowep <https://github.com/rerowep>`__)
-  circulation policy: ignore settings when deleting a policy
   `#672 <https://github.com/rero/rero-ils/pull/672>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  cli: pid fixture dependencies
   `#667 <https://github.com/rero/rero-ils/pull/667>`__
   (`rerowep <https://github.com/rerowep>`__)
-  translation: fix patron form editor translation problem
   `#666 <https://github.com/rero/rero-ils/pull/666>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  data: rewrite provisionActivity field
   `#663 <https://github.com/rero/rero-ils/pull/663>`__
   (`rerowep <https://github.com/rerowep>`__)
-  ui: add switch to professional view
   `#662 <https://github.com/rero/rero-ils/pull/662>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  serializer: remove \_settings key on aggregations
   `#660 <https://github.com/rero/rero-ils/pull/660>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  1182 - improve perf with MEF
   `#659 <https://github.com/rero/rero-ils/pull/659>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  deployment: fix pipenv version
   `#658 <https://github.com/rero/rero-ils/pull/658>`__
   (`rerowep <https://github.com/rerowep>`__)
-  translation: edition & responsability
   `#656 <https://github.com/rero/rero-ils/pull/656>`__
   (`rerowep <https://github.com/rerowep>`__)
-  travis: fix errors
   `#655 <https://github.com/rero/rero-ils/pull/655>`__
   (`rerowep <https://github.com/rerowep>`__)
-  fixtures: change library opening hours for organisation 3
   `#654 <https://github.com/rero/rero-ils/pull/654>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Us986 admin `#652 <https://github.com/rero/rero-ils/pull/652>`__
   (`jma <https://github.com/jma>`__)
-  data model: implement edition statement transformation
   `#651 <https://github.com/rero/rero-ils/pull/651>`__
   (`rerowep <https://github.com/rerowep>`__)
-  ui: correct frontpage typo
   `#647 <https://github.com/rero/rero-ils/pull/647>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  frontend: remove admin actions
   `#645 <https://github.com/rero/rero-ils/pull/645>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  cli: add new translate command
   `#643 <https://github.com/rero/rero-ils/pull/643>`__
   (`rerowep <https://github.com/rerowep>`__)
-  tests: improve test coverage
   `#640 <https://github.com/rero/rero-ils/pull/640>`__
   (`rerowep <https://github.com/rerowep>`__)
-  template: update pr template
   `#638 <https://github.com/rero/rero-ils/pull/638>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  setup: lazy creation of records
   `#635 <https://github.com/rero/rero-ils/pull/635>`__
   (`rerowep <https://github.com/rerowep>`__)
-  items: create items dump functionality
   `#634 <https://github.com/rero/rero-ils/pull/634>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  fix: correct circulation policy
   `#633 <https://github.com/rero/rero-ils/pull/633>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  permissions: allow read access to holding and items for all users
   `#632 <https://github.com/rero/rero-ils/pull/632>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  documents: fix document suppression problems
   `#631 <https://github.com/rero/rero-ils/pull/631>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  ebooks: fix ebooks dojson
   `#628 <https://github.com/rero/rero-ils/pull/628>`__
   (`rerowep <https://github.com/rerowep>`__)
-  data: Adds dump for documents
   `#618 <https://github.com/rero/rero-ils/pull/618>`__
   (`rerowep <https://github.com/rerowep>`__)
-  fix: loan and items
   `#613 <https://github.com/rero/rero-ils/pull/613>`__
   (`rerowep <https://github.com/rerowep>`__)
-  renewals: add renew buttons for patrons checked-out items
   `#610 <https://github.com/rero/rero-ils/pull/610>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  scripts: add info message coloration
   `#564 <https://github.com/rero/rero-ils/pull/564>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  circulation: fix some loan scenarios
   `#806 <https://github.com/rero/rero-ils/pull/806>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation: fix loan after a checkin of a validated request
   `#795 <https://github.com/rero/rero-ils/pull/795>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation: fix item status after a check-in
   `#782 <https://github.com/rero/rero-ils/pull/782>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  documents: Add pickup location names for the item request button
   `#779 <https://github.com/rero/rero-ils/pull/779>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  ui: display library name instead of code
   `#778 <https://github.com/rero/rero-ils/pull/778>`__
   (`jma <https://github.com/jma>`__)
-  security: authorize unsafe-eval param on script-src
   `#773 <https://github.com/rero/rero-ils/pull/773>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  ebooks: fix ebook import indexing
   `#768 <https://github.com/rero/rero-ils/pull/768>`__
   (`rerowep <https://github.com/rerowep>`__)
-  config: allow loading external script
   `#767 <https://github.com/rero/rero-ils/pull/767>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  config: allow loading inline image in the security configuration
   `#766 <https://github.com/rero/rero-ils/pull/766>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  release: v0.6.0 `#764 <https://github.com/rero/rero-ils/pull/764>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  permissions: update and delete permissions api for records
   `#760 <https://github.com/rero/rero-ils/pull/760>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  documents: update schemas about abstract field
   `#754 <https://github.com/rero/rero-ils/pull/754>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  ui: move to rero-ils-ui@0.0.10
   `#752 <https://github.com/rero/rero-ils/pull/752>`__
   (`jma <https://github.com/jma>`__)
-  circulation: correct pickup location for actions
   `#749 <https://github.com/rero/rero-ils/pull/749>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  data model: fix jsonschema for the editor
   `#746 <https://github.com/rero/rero-ils/pull/746>`__
   (`jma <https://github.com/jma>`__)
-  homepage: add homepage informations for pilot instance
   `#744 <https://github.com/rero/rero-ils/pull/744>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  ES: fix listeners
   `#738 <https://github.com/rero/rero-ils/pull/738>`__
   (`rerowep <https://github.com/rerowep>`__)
-  patrons: display checkout history for patron
   `#720 <https://github.com/rero/rero-ils/pull/720>`__
   (`BadrAly <https://github.com/BadrAly>`__)

`v0.5.2 <https://github.com/rero/rero-ils/tree/v0.5.2>`__ (2019-11-13)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.5.1...v0.5.2>`__

**Fixed bugs:**

-  Requesting an item from another organisation should not be possible
   `#619 <https://github.com/rero/rero-ils/issues/619>`__
-  Document editor: if all authors are removed from the form, then it’s
   not possible to add an author
   `#609 <https://github.com/rero/rero-ils/issues/609>`__
-  Patron creation by a librarian: reset password link never works
   `#608 <https://github.com/rero/rero-ils/issues/608>`__
-  Render a document detailed view with document even if there’s a
   library without pickup location in the organisation
   `#598 <https://github.com/rero/rero-ils/issues/598>`__

**Closed issues:**

-  Import document from BnF not working
   `#607 <https://github.com/rero/rero-ils/issues/607>`__

**Merged pull requests:**

-  dojson: fix provisionActivity unimarc transformation
   `#623 <https://github.com/rero/rero-ils/pull/623>`__
   (`jma <https://github.com/jma>`__)
-  fixtures: fix and adapt the third organisation fixtures
   `#620 <https://github.com/rero/rero-ils/pull/620>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation: fix circulation policies
   `#617 <https://github.com/rero/rero-ils/pull/617>`__
   (`jma <https://github.com/jma>`__)
-  REST API: set the aggregations size
   `#616 <https://github.com/rero/rero-ils/pull/616>`__
   (`jma <https://github.com/jma>`__)
-  circulation: cancel active loan when checked-in item has reservations
   `#615 <https://github.com/rero/rero-ils/pull/615>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Workshop Issues Fixing
   `#614 <https://github.com/rero/rero-ils/pull/614>`__
   (`jma <https://github.com/jma>`__)
-  fixtures: complete the workshop fixtures data
   `#612 <https://github.com/rero/rero-ils/pull/612>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  document editor: fix add author after removed all authors from the
   form `#611 <https://github.com/rero/rero-ils/pull/611>`__
   (`benerken <https://github.com/benerken>`__)
-  instance: fix several bugs
   `#606 <https://github.com/rero/rero-ils/pull/606>`__
   (`jma <https://github.com/jma>`__)
-  notification: fix “not extendable” string in different languages
   `#597 <https://github.com/rero/rero-ils/pull/597>`__
   (`zannkukai <https://github.com/zannkukai>`__)

`v0.5.1 <https://github.com/rero/rero-ils/tree/v0.5.1>`__ (2019-11-05)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.5.0...v0.5.1>`__

**Implemented enhancements:**

-  Flash message: bring user at top of the page
   `#232 <https://github.com/rero/rero-ils/issues/232>`__

**Fixed bugs:**

-  Not possible to add or edit a location if field is_online is not
   checked `#562 <https://github.com/rero/rero-ils/issues/562>`__
-  Fees: API returns 0 records
   `#560 <https://github.com/rero/rero-ils/issues/560>`__
-  Document editor: save button disabled
   `#556 <https://github.com/rero/rero-ils/issues/556>`__

**Closed issues:**

-  “online” item type in fixture
   `#573 <https://github.com/rero/rero-ils/issues/573>`__
-  Editor: qualifier vs. note
   `#557 <https://github.com/rero/rero-ils/issues/557>`__
-  Facet author not always displayed (in Firefox)
   `#554 <https://github.com/rero/rero-ils/issues/554>`__
-  Person page: no links to documents in organisation views
   `#553 <https://github.com/rero/rero-ils/issues/553>`__
-  Translation “The item has been requested”
   `#404 <https://github.com/rero/rero-ils/issues/404>`__

**Merged pull requests:**

-  documentation: update changes and release notes
   `#596 <https://github.com/rero/rero-ils/pull/596>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  tests: hide “No issues detected!” from autoflake
   `#595 <https://github.com/rero/rero-ils/pull/595>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  translations: update missing translations
   `#594 <https://github.com/rero/rero-ils/pull/594>`__
   (`jma <https://github.com/jma>`__)
-  ui: fix typeahead unexpected behaviour
   `#593 <https://github.com/rero/rero-ils/pull/593>`__
   (`jma <https://github.com/jma>`__)
-  editor: fix location editor button validation
   `#592 <https://github.com/rero/rero-ils/pull/592>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  translation: fix user message when an item is requested
   `#591 <https://github.com/rero/rero-ils/pull/591>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  editor: fix editor button validation
   `#590 <https://github.com/rero/rero-ils/pull/590>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  persons: fix filter to get documents in organisation views
   `#589 <https://github.com/rero/rero-ils/pull/589>`__
   (`benerken <https://github.com/benerken>`__)
-  fees: add organisation search filter
   `#588 <https://github.com/rero/rero-ils/pull/588>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  ui: fix flash messages position
   `#587 <https://github.com/rero/rero-ils/pull/587>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  fixtures: update third organisation circulation policy
   `#586 <https://github.com/rero/rero-ils/pull/586>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  ui: adapt frontpage for mobile devices
   `#585 <https://github.com/rero/rero-ils/pull/585>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  permissions: item edit and delete buttons for librarians
   `#582 <https://github.com/rero/rero-ils/pull/582>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  github: add new info on github issue template
   `#581 <https://github.com/rero/rero-ils/pull/581>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  items: fix online locations status
   `#580 <https://github.com/rero/rero-ils/pull/580>`__
   (`zannkukai <https://github.com/zannkukai>`__)

`v0.5.0 <https://github.com/rero/rero-ils/tree/v0.5.0>`__ (2019-10-23)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.4.0...v0.5.0>`__

**Fixed bugs:**

-  database sequences are not updated after executing script/setup
   `#563 <https://github.com/rero/rero-ils/issues/563>`__
-  JSON export not working
   `#547 <https://github.com/rero/rero-ils/issues/547>`__
-  A librarian should not be able to edit libraries he/she’s not
   affiliated to. `#488 <https://github.com/rero/rero-ils/issues/488>`__
-  Removing the barcode from a patron leads to an error after “Submit”
   action `#37 <https://github.com/rero/rero-ils/issues/37>`__

**Closed issues:**

-  Wrong orgnisation translation in the item type editor
   `#540 <https://github.com/rero/rero-ils/issues/540>`__
-  Internal server error when displaying record
   `#501 <https://github.com/rero/rero-ils/issues/501>`__
-  2 homepages for global view
   `#475 <https://github.com/rero/rero-ils/issues/475>`__
-  Links to items and documents from circulation UI
   `#446 <https://github.com/rero/rero-ils/issues/446>`__
-  Check the responsiveness of the front page
   `#381 <https://github.com/rero/rero-ils/issues/381>`__
-  Wrong availability for item_type “no checkout”
   `#209 <https://github.com/rero/rero-ils/issues/209>`__

**Merged pull requests:**

-  cli: reserve a range of pids
   `#579 <https://github.com/rero/rero-ils/pull/579>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  translation: correct organisation translation
   `#578 <https://github.com/rero/rero-ils/pull/578>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  ui: fix global homepage
   `#570 <https://github.com/rero/rero-ils/pull/570>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  ui: add a new URL to change the language
   `#569 <https://github.com/rero/rero-ils/pull/569>`__
   (`jma <https://github.com/jma>`__)
-  ils: translates v0.5.0 strings
   `#567 <https://github.com/rero/rero-ils/pull/567>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  permissions: disable edit and delete buttons for librarians
   `#566 <https://github.com/rero/rero-ils/pull/566>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  documentation: fill in changes and release files
   `#565 <https://github.com/rero/rero-ils/pull/565>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  fixtures: reset sequence to correct value after loading records
   `#561 <https://github.com/rero/rero-ils/pull/561>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  metadata: fix dojson for virtua records
   `#559 <https://github.com/rero/rero-ils/pull/559>`__
   (`rerowep <https://github.com/rerowep>`__)
-  ui: integrate rero-ils-ui angular project
   `#551 <https://github.com/rero/rero-ils/pull/551>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  document: fix json export
   `#548 <https://github.com/rero/rero-ils/pull/548>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  document: fix hide elements on harvested document
   `#545 <https://github.com/rero/rero-ils/pull/545>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  ebooks: enable bulk indexing of created records
   `#544 <https://github.com/rero/rero-ils/pull/544>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  fixtures: add data for a third organisation
   `#543 <https://github.com/rero/rero-ils/pull/543>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  US965: Holdings/items for ebooks
   `#537 <https://github.com/rero/rero-ils/pull/537>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)

`v0.4.0 <https://github.com/rero/rero-ils/tree/v0.4.0>`__ (2019-09-30)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.3.1...v0.4.0>`__

**Implemented enhancements:**

-  Checkin/checkout tab top text
   `#366 <https://github.com/rero/rero-ils/issues/366>`__

**Fixed bugs:**

-  Thumbnails detail view
   `#495 <https://github.com/rero/rero-ils/issues/495>`__
-  Two loans instead of one
   `#484 <https://github.com/rero/rero-ils/issues/484>`__
-  Detailed view: field “Notes” is displayed with no content
   `#437 <https://github.com/rero/rero-ils/issues/437>`__
-  Increase size of result set during API calls
   `#405 <https://github.com/rero/rero-ils/issues/405>`__
-  Display of “My account”
   `#225 <https://github.com/rero/rero-ils/issues/225>`__
-  UX of date exceptions
   `#223 <https://github.com/rero/rero-ils/issues/223>`__

**Closed issues:**

-  Checkin of item that should go in transit
   `#462 <https://github.com/rero/rero-ils/issues/462>`__
-  Mousehover on “Delete”, when the item cannot be deleted
   `#447 <https://github.com/rero/rero-ils/issues/447>`__
-  Availability light in views
   `#445 <https://github.com/rero/rero-ils/issues/445>`__
-  Checkout for the end of a day (23h59)
   `#417 <https://github.com/rero/rero-ils/issues/417>`__
-  Merge public and professional document search views.
   `#383 <https://github.com/rero/rero-ils/issues/383>`__
-  Improve test and test coverage
   `#380 <https://github.com/rero/rero-ils/issues/380>`__
-  Upgrade to the latest version of invenio-circulation
   `#379 <https://github.com/rero/rero-ils/issues/379>`__
-  Transaction library instead of item library
   `#378 <https://github.com/rero/rero-ils/issues/378>`__
-  Circulation UI: items & patrons of other organisation
   `#377 <https://github.com/rero/rero-ils/issues/377>`__
-  Change license headers
   `#374 <https://github.com/rero/rero-ils/issues/374>`__
-  Fix circ policies editor
   `#363 <https://github.com/rero/rero-ils/issues/363>`__
-  [angular] Handle Error if http client doesn’t response
   `#167 <https://github.com/rero/rero-ils/issues/167>`__

**Merged pull requests:**

-  tests: add PID verifications with commit/rollback
   `#558 <https://github.com/rero/rero-ils/pull/558>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  #1021 - refactoring: delete unused imports
   `#536 <https://github.com/rero/rero-ils/pull/536>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  data: new data files for MEF
   `#535 <https://github.com/rero/rero-ils/pull/535>`__
   (`rerowep <https://github.com/rerowep>`__)
-  docker: update elasticsearch and kibana to version 6.6.2
   `#534 <https://github.com/rero/rero-ils/pull/534>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  circulation : fix checkin of item that should go in transit
   `#533 <https://github.com/rero/rero-ils/pull/533>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  form options (for ebook): item type and location for online status
   `#532 <https://github.com/rero/rero-ils/pull/532>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  document: display holding electronic location
   `#531 <https://github.com/rero/rero-ils/pull/531>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  US696: overdue fees
   `#530 <https://github.com/rero/rero-ils/pull/530>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  editor: fix submit button with async validator
   `#528 <https://github.com/rero/rero-ils/pull/528>`__
   (`jma <https://github.com/jma>`__)
-  US931 data model publication statement
   `#526 <https://github.com/rero/rero-ils/pull/526>`__
   (`rerowep <https://github.com/rerowep>`__)
-  ebooks: create holdings automatically after record harvesting
   `#525 <https://github.com/rero/rero-ils/pull/525>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  #971 - ui: display git commit hash on frontpage
   `#524 <https://github.com/rero/rero-ils/pull/524>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  #1027 - item availability instead of status
   `#523 <https://github.com/rero/rero-ils/pull/523>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  documents: fix language
   `#522 <https://github.com/rero/rero-ils/pull/522>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  data model: implement publication statement transformation for ebooks
   `#521 <https://github.com/rero/rero-ils/pull/521>`__
   (`reropag <https://github.com/reropag>`__)
-  ui: fix front page responsiveness #381
   `#520 <https://github.com/rero/rero-ils/pull/520>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  ui: adapt editor according to publication statement data model
   `#519 <https://github.com/rero/rero-ils/pull/519>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  schema: make the name for publisher optional
   `#518 <https://github.com/rero/rero-ils/pull/518>`__
   (`jma <https://github.com/jma>`__)
-  ui: correct document brief views
   `#517 <https://github.com/rero/rero-ils/pull/517>`__
   (`rerowep <https://github.com/rerowep>`__)
-  documentation: add a default issue template
   `#516 <https://github.com/rero/rero-ils/pull/516>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  tests: fix external tests after availability implementation
   `#515 <https://github.com/rero/rero-ils/pull/515>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  UI:display the publication statement
   `#514 <https://github.com/rero/rero-ils/pull/514>`__
   (`rerowep <https://github.com/rerowep>`__)
-  check email templates
   `#513 <https://github.com/rero/rero-ils/pull/513>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  circulation : fix checkin of item that should go in transit
   `#512 <https://github.com/rero/rero-ils/pull/512>`__
   (`benerken <https://github.com/benerken>`__)
-  publication statement es
   `#511 <https://github.com/rero/rero-ils/pull/511>`__
   (`rerowep <https://github.com/rerowep>`__)
-  document: fix default icon thumbnail on fullview
   `#510 <https://github.com/rero/rero-ils/pull/510>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  circ_policies ui: increase API size limit
   `#509 <https://github.com/rero/rero-ils/pull/509>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  scripts: wrong command in server script
   `#508 <https://github.com/rero/rero-ils/pull/508>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  libraries: fix start date of reroils fixtures
   `#507 <https://github.com/rero/rero-ils/pull/507>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  #1036 - bootstrap: delete useless virtualenv
   `#506 <https://github.com/rero/rero-ils/pull/506>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  US911 cataloging `#504 <https://github.com/rero/rero-ils/pull/504>`__
   (`jma <https://github.com/jma>`__)
-  fixture: implement ebooks holdings rero-ils and unit test fixtures
   `#503 <https://github.com/rero/rero-ils/pull/503>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  UI: Fix circulation policies editor #363
   `#500 <https://github.com/rero/rero-ils/pull/500>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  holdings: display holdings records
   `#499 <https://github.com/rero/rero-ils/pull/499>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  publication statement bnf
   `#498 <https://github.com/rero/rero-ils/pull/498>`__
   (`rerowep <https://github.com/rerowep>`__)
-  #1019 - Refactoring units testing api calls
   `#497 <https://github.com/rero/rero-ils/pull/497>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  circulation : fix issue two loans instead of one
   `#496 <https://github.com/rero/rero-ils/pull/496>`__
   (`benerken <https://github.com/benerken>`__)
-  Publication statement view
   `#494 <https://github.com/rero/rero-ils/pull/494>`__
   (`AoNoOokami <https://github.com/AoNoOokami>`__)
-  validate json file with schema
   `#493 <https://github.com/rero/rero-ils/pull/493>`__
   (`rerowep <https://github.com/rerowep>`__)
-  US838: display record availability
   `#491 <https://github.com/rero/rero-ils/pull/491>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Fee: better currency management
   `#490 <https://github.com/rero/rero-ils/pull/490>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  documents: implement record availability
   `#489 <https://github.com/rero/rero-ils/pull/489>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  #1011 fix unittest fixtures
   `#487 <https://github.com/rero/rero-ils/pull/487>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  interface: display record availability in document detailed view
   `#486 <https://github.com/rero/rero-ils/pull/486>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  publication statement transformation
   `#485 <https://github.com/rero/rero-ils/pull/485>`__
   (`reropag <https://github.com/reropag>`__)
-  Fees: create new resource
   `#482 <https://github.com/rero/rero-ils/pull/482>`__
   (`lauren-d <https://github.com/lauren-d>`__)
-  installation: fix bootstrap script to use npm 6 instead of local one
   `#481 <https://github.com/rero/rero-ils/pull/481>`__
   (`blankoworld <https://github.com/blankoworld>`__)
-  holdings: implement record availability
   `#480 <https://github.com/rero/rero-ils/pull/480>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation_ui: add error logs for item API
   `#479 <https://github.com/rero/rero-ils/pull/479>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  interface: item availability
   `#478 <https://github.com/rero/rero-ils/pull/478>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  document detailed view: fix missing message on item delete button
   `#477 <https://github.com/rero/rero-ils/pull/477>`__
   (`zannkukai <https://github.com/zannkukai>`__)
-  fix user initials view
   `#476 <https://github.com/rero/rero-ils/pull/476>`__
   (`rerowep <https://github.com/rerowep>`__)
-  editor: shows/hides main (1th level) fields
   `#473 <https://github.com/rero/rero-ils/pull/473>`__
   (`jma <https://github.com/jma>`__)
-  fixtures: generate new files
   `#472 <https://github.com/rero/rero-ils/pull/472>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: standardize timezone
   `#471 <https://github.com/rero/rero-ils/pull/471>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  data_model: implement copyright date transformation
   `#470 <https://github.com/rero/rero-ils/pull/470>`__
   (`reropag <https://github.com/reropag>`__)
-  circulation ui: check if item or patron is in same organisation
   `#469 <https://github.com/rero/rero-ils/pull/469>`__
   (`jma <https://github.com/jma>`__)
-  fixtures: fixes slowness of setup after holding integration
   `#468 <https://github.com/rero/rero-ils/pull/468>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  data_model: implement copyright date transformation
   `#466 <https://github.com/rero/rero-ils/pull/466>`__
   (`reropag <https://github.com/reropag>`__)
-  circulation ui: enhancement on the text of tab (checkin/checkout)
   `#465 <https://github.com/rero/rero-ils/pull/465>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  libraries date exceptions: fix bug on repeat button
   `#463 <https://github.com/rero/rero-ils/pull/463>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  circulation: holdings level adaptation
   `#461 <https://github.com/rero/rero-ils/pull/461>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation ui: check if item or patron is in same organisation
   `#460 <https://github.com/rero/rero-ils/pull/460>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  US716 holdings level
   `#458 <https://github.com/rero/rero-ils/pull/458>`__
   (`BadrAly <https://github.com/BadrAly>`__)

`v0.3.1 <https://github.com/rero/rero-ils/tree/v0.3.1>`__ (2019-08-26)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.3.0...v0.3.1>`__

**Merged pull requests:**

-  translation: fix missing translated strings
   `#459 <https://github.com/rero/rero-ils/pull/459>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  holdings: re-linking item to a new holding after edition
   `#457 <https://github.com/rero/rero-ils/pull/457>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  oaiharvesting: bulk indexing of oai records
   `#456 <https://github.com/rero/rero-ils/pull/456>`__
   (`rerowep <https://github.com/rerowep>`__)
-  release: v0.3.0 `#454 <https://github.com/rero/rero-ils/pull/454>`__
   (`jma <https://github.com/jma>`__)

`v0.3.0 <https://github.com/rero/rero-ils/tree/v0.3.0>`__ (2019-08-22)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.2.3...v0.3.0>`__

**Implemented enhancements:**

-  Should ebooks records be editable ?
   `#89 <https://github.com/rero/rero-ils/issues/89>`__

**Fixed bugs:**

-  Edit item button in professional document search view always visible
   `#390 <https://github.com/rero/rero-ils/issues/390>`__
-  Due date in a check-out does not consider closed days introduced in
   exceptions `#263 <https://github.com/rero/rero-ils/issues/263>`__

**Closed issues:**

-  Layout of confirmation message when deleting an item
   `#407 <https://github.com/rero/rero-ils/issues/407>`__
-  Search with AND operator does not work as expected.
   `#384 <https://github.com/rero/rero-ils/issues/384>`__
-  Search in various fields
   `#369 <https://github.com/rero/rero-ils/issues/369>`__
-  gnd_pid / pid `#352 <https://github.com/rero/rero-ils/issues/352>`__
-  [editor] location name selector in the item editor
   `#348 <https://github.com/rero/rero-ils/issues/348>`__

**Merged pull requests:**

-  holdings: adapt item display
   `#455 <https://github.com/rero/rero-ils/pull/455>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  translations: translate v0.3.0 release strings
   `#453 <https://github.com/rero/rero-ils/pull/453>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  circulation ui: view code on document and item link
   `#452 <https://github.com/rero/rero-ils/pull/452>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  tests: test correct licenses in files
   `#451 <https://github.com/rero/rero-ils/pull/451>`__
   (`rerowep <https://github.com/rerowep>`__)
-  tests: fix dependencies on travis
   `#450 <https://github.com/rero/rero-ils/pull/450>`__
   (`jma <https://github.com/jma>`__)
-  circulation: due date hours set to end of day
   `#449 <https://github.com/rero/rero-ils/pull/449>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  admin: Wrong organisation on select menu
   `#448 <https://github.com/rero/rero-ils/pull/448>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  item: fix display of the buttons
   `#444 <https://github.com/rero/rero-ils/pull/444>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  holdings: introduce holding level
   `#443 <https://github.com/rero/rero-ils/pull/443>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  document: fix notes field
   `#441 <https://github.com/rero/rero-ils/pull/441>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  notifications: url of the account of the notified patron
   `#439 <https://github.com/rero/rero-ils/pull/439>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  ui: facet language translation
   `#438 <https://github.com/rero/rero-ils/pull/438>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  circulation: upgrade to invenio-circulation v1.0.0a16
   `#436 <https://github.com/rero/rero-ils/pull/436>`__
   (`reropag <https://github.com/reropag>`__)
-  ui: facet language translation
   `#435 <https://github.com/rero/rero-ils/pull/435>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  editor: compact the presentation
   `#434 <https://github.com/rero/rero-ils/pull/434>`__
   (`jma <https://github.com/jma>`__)
-  license: move from GPLv2 to AGPLv3
   `#433 <https://github.com/rero/rero-ils/pull/433>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3
   `#432 <https://github.com/rero/rero-ils/pull/432>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3
   `#431 <https://github.com/rero/rero-ils/pull/431>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  data model: language, identifiedBy
   `#430 <https://github.com/rero/rero-ils/pull/430>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  license: move from GPLv2 to AGPLv3
   `#429 <https://github.com/rero/rero-ils/pull/429>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3
   `#428 <https://github.com/rero/rero-ils/pull/428>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3
   `#427 <https://github.com/rero/rero-ils/pull/427>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  fix 10k items `#426 <https://github.com/rero/rero-ils/pull/426>`__
   (`rerowep <https://github.com/rerowep>`__)
-  license: move from GPLv2 to AGPLv3
   `#425 <https://github.com/rero/rero-ils/pull/425>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3
   `#424 <https://github.com/rero/rero-ils/pull/424>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  data mode: adapt editor for language and identifiedBy
   `#423 <https://github.com/rero/rero-ils/pull/423>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  data model: adapt document views for language and identifiedby
   `#422 <https://github.com/rero/rero-ils/pull/422>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  cli: replaces invenio records by invenio fixtures
   `#421 <https://github.com/rero/rero-ils/pull/421>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  update fixtures `#420 <https://github.com/rero/rero-ils/pull/420>`__
   (`rerowep <https://github.com/rerowep>`__)
-  ui: Implement global and organisations view
   `#419 <https://github.com/rero/rero-ils/pull/419>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  data model: schema and mapping and unit testing adaptation for
   languages `#418 <https://github.com/rero/rero-ils/pull/418>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  data model: transform languages
   `#416 <https://github.com/rero/rero-ils/pull/416>`__
   (`reropag <https://github.com/reropag>`__)
-  data model: transform marc21 field containing identifiers
   `#415 <https://github.com/rero/rero-ils/pull/415>`__
   (`reropag <https://github.com/reropag>`__)
-  data model: schema and mapping and unit testing adaptation for
   identifiedby `#414 <https://github.com/rero/rero-ils/pull/414>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  ui: fix bad alignment in delete item modal header
   `#413 <https://github.com/rero/rero-ils/pull/413>`__
   (`jma <https://github.com/jma>`__)
-  security: update to invenio version 3.1.1
   `#412 <https://github.com/rero/rero-ils/pull/412>`__
   (`rerowep <https://github.com/rerowep>`__)
-  tests: optional execution of external services tests.
   `#411 <https://github.com/rero/rero-ils/pull/411>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  indexation class: add indexation property to IlsRecord
   `#409 <https://github.com/rero/rero-ils/pull/409>`__
   (`rerowep <https://github.com/rerowep>`__)
-  tests: workaround when bnf service is down
   `#403 <https://github.com/rero/rero-ils/pull/403>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  documentation: update INSTALL.rst
   `#402 <https://github.com/rero/rero-ils/pull/402>`__
   (`vrabe <https://github.com/vrabe>`__)
-  search: Replace AND default operator by OR.
   `#401 <https://github.com/rero/rero-ils/pull/401>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  license: move from GPLv2 to AGPLv3 (MEF Persons)
   `#399 <https://github.com/rero/rero-ils/pull/399>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (locations)
   `#398 <https://github.com/rero/rero-ils/pull/398>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (loans)
   `#397 <https://github.com/rero/rero-ils/pull/397>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (libraries)
   `#396 <https://github.com/rero/rero-ils/pull/396>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (items)
   `#394 <https://github.com/rero/rero-ils/pull/394>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (item_types)
   `#393 <https://github.com/rero/rero-ils/pull/393>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (ebooks)
   `#392 <https://github.com/rero/rero-ils/pull/392>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (documents)
   `#391 <https://github.com/rero/rero-ils/pull/391>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (circ_pol)
   `#388 <https://github.com/rero/rero-ils/pull/388>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  license: move from GPLv2 to AGPLv3 (base commit)
   `#387 <https://github.com/rero/rero-ils/pull/387>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  documentation: add an issue template
   `#386 <https://github.com/rero/rero-ils/pull/386>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  documentation: rewrite bad syntax in docstrings
   `#382 <https://github.com/rero/rero-ils/pull/382>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)

`v0.2.3 <https://github.com/rero/rero-ils/tree/v0.2.3>`__ (2019-07-03)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.2.2...v0.2.3>`__

**Fixed bugs:**

-  TypeError: ‘NoneType’ object is not iterable
   `#367 <https://github.com/rero/rero-ils/issues/367>`__

**Closed issues:**

-  Fixtures: write a better and faster way to create circulation
   transactions `#254 <https://github.com/rero/rero-ils/issues/254>`__

**Merged pull requests:**

-  fixtures: fix dojson publishers conversion (3rd time)
   `#373 <https://github.com/rero/rero-ils/pull/373>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  release v0.2.0 `#362 <https://github.com/rero/rero-ils/pull/362>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)

`v0.2.2 <https://github.com/rero/rero-ils/tree/v0.2.2>`__ (2019-07-02)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.2.1...v0.2.2>`__

**Fixed bugs:**

-  Wrong patron displayed when checking in a requested item
   `#357 <https://github.com/rero/rero-ils/issues/357>`__
-  MultipleLoansOnItemError
   `#355 <https://github.com/rero/rero-ils/issues/355>`__

**Merged pull requests:**

-  circulation: improve circulation dates
   `#375 <https://github.com/rero/rero-ils/pull/375>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  document: Publisher format
   `#371 <https://github.com/rero/rero-ils/pull/371>`__
   (`sebastiendeleze <https://github.com/sebastiendeleze>`__)

`v0.2.1 <https://github.com/rero/rero-ils/tree/v0.2.1>`__ (2019-07-01)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.2.0...v0.2.1>`__

**Implemented enhancements:**

-  Facets: add a “more” link or button.
   `#87 <https://github.com/rero/rero-ils/issues/87>`__

**Fixed bugs:**

-  Patron search doesn’t work as expected
   `#229 <https://github.com/rero/rero-ils/issues/229>`__

**Closed issues:**

-  Unnecessary links on ebooks frontpage
   `#353 <https://github.com/rero/rero-ils/issues/353>`__
-  Space missing in toast message (only IT and DE)
   `#273 <https://github.com/rero/rero-ils/issues/273>`__

**Merged pull requests:**

-  fixture: fix transformation with no publishers
   `#368 <https://github.com/rero/rero-ils/pull/368>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  facets: expand facet items by link
   `#364 <https://github.com/rero/rero-ils/pull/364>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)

`v0.2.0 <https://github.com/rero/rero-ils/tree/v0.2.0>`__ (2019-06-27)
----------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.1.0a22...v0.2.0>`__

**Implemented enhancements:**

-  Number of occurrences is wrong in facet “status”
   `#10 <https://github.com/rero/rero-ils/issues/10>`__

**Fixed bugs:**

-  Item location not populated in item editor
   `#217 <https://github.com/rero/rero-ils/issues/217>`__
-  Title missing in e-mail sent to patron
   `#52 <https://github.com/rero/rero-ils/issues/52>`__

**Closed issues:**

-  [UI] Languages selector
   `#349 <https://github.com/rero/rero-ils/issues/349>`__
-  Delete on record: check during delete
   `#145 <https://github.com/rero/rero-ils/issues/145>`__
-  Upper and lower case, singular and plural forms
   `#119 <https://github.com/rero/rero-ils/issues/119>`__

**Merged pull requests:**

-  circulation: upgrade to invenio circulation v1.0.0a14
   `#410 <https://github.com/rero/rero-ils/pull/410>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  issues: fix issue when wrong patron displayed after a checkin
   `#370 <https://github.com/rero/rero-ils/pull/370>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  ui: update translations for v.0.2.0 release
   `#361 <https://github.com/rero/rero-ils/pull/361>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  document: MEF variant_name for author
   `#360 <https://github.com/rero/rero-ils/pull/360>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  document: call_number on item
   `#359 <https://github.com/rero/rero-ils/pull/359>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Fixtures: dojson RDA transformation
   `#358 <https://github.com/rero/rero-ils/pull/358>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  serializer: permissions on a non-existing record
   `#356 <https://github.com/rero/rero-ils/pull/356>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  [UI] Languages selector
   `#354 <https://github.com/rero/rero-ils/pull/354>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Us671 search and ranking
   `#351 <https://github.com/rero/rero-ils/pull/351>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  notification: create notification templates
   `#350 <https://github.com/rero/rero-ils/pull/350>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  US341: Email notifications
   `#347 <https://github.com/rero/rero-ils/pull/347>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  notifications: split notifications es and creations tests.
   `#346 <https://github.com/rero/rero-ils/pull/346>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  US738: Three default roles for the minimal consortial model
   `#345 <https://github.com/rero/rero-ils/pull/345>`__
   (`jma <https://github.com/jma>`__)
-  UI: adapt the patron editor for the logged user
   `#344 <https://github.com/rero/rero-ils/pull/344>`__
   (`jma <https://github.com/jma>`__)
-  notifications: create periodic task to create and send notifications
   `#343 <https://github.com/rero/rero-ils/pull/343>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  search: boosting fields on resources
   `#342 <https://github.com/rero/rero-ils/pull/342>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  notifications: complete units tests
   `#341 <https://github.com/rero/rero-ils/pull/341>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  notifications: create notification dispatcher
   `#340 <https://github.com/rero/rero-ils/pull/340>`__
   (`rerowep <https://github.com/rerowep>`__)
-  notifications: first reminder notification
   `#339 <https://github.com/rero/rero-ils/pull/339>`__
   (`reropag <https://github.com/reropag>`__)
-  indexing: update document and ebooks mapping
   `#338 <https://github.com/rero/rero-ils/pull/338>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  notifications: create due soon notification
   `#336 <https://github.com/rero/rero-ils/pull/336>`__
   (`reropag <https://github.com/reropag>`__)
-  indexing: update circulation policies mapping
   `#335 <https://github.com/rero/rero-ils/pull/335>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  indexing: update mef persons mapping
   `#333 <https://github.com/rero/rero-ils/pull/333>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  notifications: create availability notification
   `#332 <https://github.com/rero/rero-ils/pull/332>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  notifications: create recall notification
   `#331 <https://github.com/rero/rero-ils/pull/331>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  indexing: update libraries mapping
   `#330 <https://github.com/rero/rero-ils/pull/330>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  REST API: add permission informations
   `#329 <https://github.com/rero/rero-ils/pull/329>`__
   (`jma <https://github.com/jma>`__)
-  notification: circ policies new parameters
   `#328 <https://github.com/rero/rero-ils/pull/328>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  tests: add several users for testing
   `#327 <https://github.com/rero/rero-ils/pull/327>`__
   (`jma <https://github.com/jma>`__)
-  notifications: create data model and api
   `#326 <https://github.com/rero/rero-ils/pull/326>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  indexing: update patrons mapping
   `#325 <https://github.com/rero/rero-ils/pull/325>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  indexing: update patron types mapping
   `#324 <https://github.com/rero/rero-ils/pull/324>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  permissions: allows librarian to manipulate users of its library only
   `#323 <https://github.com/rero/rero-ils/pull/323>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  indexing: update item types mapping
   `#322 <https://github.com/rero/rero-ils/pull/322>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)

`v0.1.0a22 <https://github.com/rero/rero-ils/tree/v0.1.0a22>`__ (2019-05-28)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.1.0a21...v0.1.0a22>`__

**Implemented enhancements:**

-  OAI config file loding YAMLLoadWarning
   `#304 <https://github.com/rero/rero-ils/issues/304>`__
-  Renewal date `#231 <https://github.com/rero/rero-ils/issues/231>`__
-  Check-out of an item “in transit”
   `#230 <https://github.com/rero/rero-ils/issues/230>`__
-  Field “Description”
   `#224 <https://github.com/rero/rero-ils/issues/224>`__
-  Overlap of opening hours
   `#222 <https://github.com/rero/rero-ils/issues/222>`__
-  Date exceptions : repeat
   `#155 <https://github.com/rero/rero-ils/issues/155>`__
-  Header not auto-hide sticky for circulation pages
   `#144 <https://github.com/rero/rero-ils/issues/144>`__
-  Action delete on record
   `#142 <https://github.com/rero/rero-ils/issues/142>`__

**Fixed bugs:**

-  Link from person detailed page to document
   `#295 <https://github.com/rero/rero-ils/issues/295>`__
-  Request on an item which is checked out
   `#235 <https://github.com/rero/rero-ils/issues/235>`__
-  Socket closed in worker
   `#82 <https://github.com/rero/rero-ils/issues/82>`__
-  Wrong circulation status after checkin
   `#51 <https://github.com/rero/rero-ils/issues/51>`__

**Closed issues:**

-  Missing message to the librarian when a requested item is checked in
   `#58 <https://github.com/rero/rero-ils/issues/58>`__
-  A request should block the renewal
   `#38 <https://github.com/rero/rero-ils/issues/38>`__

**Merged pull requests:**

-  indexing: add a custom text analyzer in ES template
   `#321 <https://github.com/rero/rero-ils/pull/321>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  API: Patron creation problem
   `#320 <https://github.com/rero/rero-ils/pull/320>`__
   (`jma <https://github.com/jma>`__)
-  fix: document with items failure to display
   `#319 <https://github.com/rero/rero-ils/pull/319>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  fix: patron persistent identifiers
   `#318 <https://github.com/rero/rero-ils/pull/318>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  release: v0.1.0a22
   `#317 <https://github.com/rero/rero-ils/pull/317>`__
   (`jma <https://github.com/jma>`__)
-  permissions: secure patron records api
   `#316 <https://github.com/rero/rero-ils/pull/316>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Fix ebook unknown language and subject facets
   `#315 <https://github.com/rero/rero-ils/pull/315>`__
   (`rerowep <https://github.com/rerowep>`__)
-  US717 and 778 `#313 <https://github.com/rero/rero-ils/pull/313>`__
   (`jma <https://github.com/jma>`__)
-  documentation: update commit message template
   `#312 <https://github.com/rero/rero-ils/pull/312>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  user roles: system librarian role
   `#311 <https://github.com/rero/rero-ils/pull/311>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  config: Sentry support
   `#310 <https://github.com/rero/rero-ils/pull/310>`__
   (`jma <https://github.com/jma>`__)
-  US737: Two organisations for the minimal consortial model
   `#308 <https://github.com/rero/rero-ils/pull/308>`__
   (`jma <https://github.com/jma>`__)
-  tasks: celery version constraint addition
   `#307 <https://github.com/rero/rero-ils/pull/307>`__
   (`jma <https://github.com/jma>`__)
-  views: disabling edit/delete buttons for items of other organisation
   `#306 <https://github.com/rero/rero-ils/pull/306>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  cli: loan fixtures generation for organisations
   `#302 <https://github.com/rero/rero-ils/pull/302>`__
   (`jma <https://github.com/jma>`__)
-  rest API: access restriction by organisation read, write, delete,
   update `#301 <https://github.com/rero/rero-ils/pull/301>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  cli: item fixtures generation for organisations
   `#300 <https://github.com/rero/rero-ils/pull/300>`__
   (`jma <https://github.com/jma>`__)
-  fix: patron type pid shortcut
   `#299 <https://github.com/rero/rero-ils/pull/299>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  fixtures: load prepared loans json file
   `#296 <https://github.com/rero/rero-ils/pull/296>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: test coverage and docs for non modules
   `#294 <https://github.com/rero/rero-ils/pull/294>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: test coverage and docs for documents
   `#293 <https://github.com/rero/rero-ils/pull/293>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: test coverage and docs for loans
   `#292 <https://github.com/rero/rero-ils/pull/292>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  rest API: organisation filter
   `#291 <https://github.com/rero/rero-ils/pull/291>`__
   (`jma <https://github.com/jma>`__)
-  global: test coverage and docs for patrons
   `#290 <https://github.com/rero/rero-ils/pull/290>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: test coverage and docs for items
   `#289 <https://github.com/rero/rero-ils/pull/289>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: test coverage and docs for libraries
   `#288 <https://github.com/rero/rero-ils/pull/288>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  consortium: metada for two organisations
   `#287 <https://github.com/rero/rero-ils/pull/287>`__
   (`jma <https://github.com/jma>`__)
-  consortium: second organisation metadata.
   `#284 <https://github.com/rero/rero-ils/pull/284>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: test coverage and docs for organisations
   `#283 <https://github.com/rero/rero-ils/pull/283>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: test coverage and docs for locations
   `#282 <https://github.com/rero/rero-ils/pull/282>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation: correct item status after checkin a requested item
   `#281 <https://github.com/rero/rero-ils/pull/281>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  user interface: patron type name and library name
   `#280 <https://github.com/rero/rero-ils/pull/280>`__
   (`jma <https://github.com/jma>`__)
-  global: test coverage and docs for patron types
   `#279 <https://github.com/rero/rero-ils/pull/279>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  user interface: pickup library instead of pickup location
   `#278 <https://github.com/rero/rero-ils/pull/278>`__
   (`jma <https://github.com/jma>`__)
-  global: test coverage and docs for item types
   `#277 <https://github.com/rero/rero-ils/pull/277>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  global: test coverage and docs for cipo
   `#276 <https://github.com/rero/rero-ils/pull/276>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation: patron request blocks item renewals
   `#274 <https://github.com/rero/rero-ils/pull/274>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  fix: a fix for loan extension assert problem
   `#272 <https://github.com/rero/rero-ils/pull/272>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Delete add item button in the document search view
   `#268 <https://github.com/rero/rero-ils/pull/268>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  circulation: possibility to check-out in-transit items
   `#267 <https://github.com/rero/rero-ils/pull/267>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  circulation: renewal due date from current_date
   `#265 <https://github.com/rero/rero-ils/pull/265>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  ui: library exception button
   `#261 <https://github.com/rero/rero-ils/pull/261>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  ui: notification `#258 <https://github.com/rero/rero-ils/pull/258>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  library exceptions date: improvement
   `#257 <https://github.com/rero/rero-ils/pull/257>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Circulation: renewal due date from current_date
   `#256 <https://github.com/rero/rero-ils/pull/256>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  ALL: invenio 3.1 support
   `#255 <https://github.com/rero/rero-ils/pull/255>`__
   (`jma <https://github.com/jma>`__)
-  admin: field description not mandatory
   `#253 <https://github.com/rero/rero-ils/pull/253>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  library admin: improvement
   `#251 <https://github.com/rero/rero-ils/pull/251>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)

`v0.1.0a21 <https://github.com/rero/rero-ils/tree/v0.1.0a21>`__ (2019-03-28)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.1.0a20...v0.1.0a21>`__

**Implemented enhancements:**

-  Redirect to document detailed view after document or item edition.
   `#226 <https://github.com/rero/rero-ils/issues/226>`__
-  Identify the two separate displays in the person detailed view
   `#137 <https://github.com/rero/rero-ils/issues/137>`__
-  mef id for person not on same line
   `#131 <https://github.com/rero/rero-ils/issues/131>`__
-  Pager not to display if only 1 page of results
   `#123 <https://github.com/rero/rero-ils/issues/123>`__
-  pytest Elasticsearch
   `#114 <https://github.com/rero/rero-ils/issues/114>`__
-  Years facet behaviour
   `#92 <https://github.com/rero/rero-ils/issues/92>`__
-  Status “Not available” when item is missing
   `#47 <https://github.com/rero/rero-ils/issues/47>`__
-  No button to return to the view we come from (like “Back to the
   results” for example)
   `#36 <https://github.com/rero/rero-ils/issues/36>`__
-  Items with active transactions can be deleted without any warning
   `#34 <https://github.com/rero/rero-ils/issues/34>`__
-  Record deletion without checking the attached records
   `#12 <https://github.com/rero/rero-ils/issues/12>`__

**Fixed bugs:**

-  Link from item view to patron check-in/check-out broken
   `#234 <https://github.com/rero/rero-ils/issues/234>`__
-  Circulation UI: “an error occurs on the server: [object Object]”
   `#233 <https://github.com/rero/rero-ils/issues/233>`__
-  No check when deleting ptty and itty, resulting in broken cipo.
   `#227 <https://github.com/rero/rero-ils/issues/227>`__
-  Creation of a library: fields already completed
   `#221 <https://github.com/rero/rero-ils/issues/221>`__
-  Request menu don’t display the pickup_name field
   `#170 <https://github.com/rero/rero-ils/issues/170>`__
-  After signing up, all pages respond with an internal server error.
   `#164 <https://github.com/rero/rero-ils/issues/164>`__
-  Saved item type
   `#143 <https://github.com/rero/rero-ils/issues/143>`__
-  mef id for person not on same line
   `#131 <https://github.com/rero/rero-ils/issues/131>`__
-  brief view for logged user not reliable
   `#129 <https://github.com/rero/rero-ils/issues/129>`__
-  Covers not displaying
   `#120 <https://github.com/rero/rero-ils/issues/120>`__
-  Result list, page browse
   `#117 <https://github.com/rero/rero-ils/issues/117>`__
-  Simple search does not return some results
   `#93 <https://github.com/rero/rero-ils/issues/93>`__
-  A new search should remove all filters
   `#88 <https://github.com/rero/rero-ils/issues/88>`__
-  deduplication of uri
   `#84 <https://github.com/rero/rero-ils/issues/84>`__
-  Availabilty information message not translated on the search results
   page `#54 <https://github.com/rero/rero-ils/issues/54>`__
-  Broken link in circulation table
   `#50 <https://github.com/rero/rero-ils/issues/50>`__
-  Patron without barcode
   `#48 <https://github.com/rero/rero-ils/issues/48>`__
-  Links to library/member or location detailed view as a patron
   `#43 <https://github.com/rero/rero-ils/issues/43>`__
-  Confirmation message after record creation
   `#40 <https://github.com/rero/rero-ils/issues/40>`__
-  Lost password workflow only in English
   `#3 <https://github.com/rero/rero-ils/issues/3>`__

**Closed issues:**

-  Admin resources menu : harmonize editor headings texts
   `#215 <https://github.com/rero/rero-ils/issues/215>`__
-  Date exception: not translated
   `#163 <https://github.com/rero/rero-ils/issues/163>`__
-  Item and Patron fixtures to reflect the new item/patron types
   `#126 <https://github.com/rero/rero-ils/issues/126>`__
-  Layouts issues and remarks
   `#121 <https://github.com/rero/rero-ils/issues/121>`__
-  Person search brief view: some information missing
   `#118 <https://github.com/rero/rero-ils/issues/118>`__
-  Edit buttons (translations)
   `#76 <https://github.com/rero/rero-ils/issues/76>`__
-  location validation for items
   `#70 <https://github.com/rero/rero-ils/issues/70>`__
-  Change the color of the “circulation transaction creation” print
   confirmation message
   `#64 <https://github.com/rero/rero-ils/issues/64>`__
-  Missing translation of “requested items”
   `#56 <https://github.com/rero/rero-ils/issues/56>`__
-  Flash notification for “in transit” at checkin
   `#49 <https://github.com/rero/rero-ils/issues/49>`__
-  Default sort of demand list
   `#45 <https://github.com/rero/rero-ils/issues/45>`__
-  Scope of search bar not always visible
   `#39 <https://github.com/rero/rero-ils/issues/39>`__
-  Search by patron_full_name does not check the role “patrons”
   `#29 <https://github.com/rero/rero-ils/issues/29>`__
-  renewal counts `#28 <https://github.com/rero/rero-ils/issues/28>`__

**Merged pull requests:**

-  API: subject facet resolution
   `#250 <https://github.com/rero/rero-ils/pull/250>`__
   (`jma <https://github.com/jma>`__)
-  translations: version v.0.1.0a21
   `#249 <https://github.com/rero/rero-ils/pull/249>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  DEPLOY: autocomplete resolution for deployement
   `#248 <https://github.com/rero/rero-ils/pull/248>`__
   (`jma <https://github.com/jma>`__)
-  TRANSLATIONS: translations command line resolution
   `#247 <https://github.com/rero/rero-ils/pull/247>`__
   (`jma <https://github.com/jma>`__)
-  UI: editor previous page redirection
   `#246 <https://github.com/rero/rero-ils/pull/246>`__
   (`jma <https://github.com/jma>`__)
-  UI: clear library form after edit
   `#245 <https://github.com/rero/rero-ils/pull/245>`__
   (`jma <https://github.com/jma>`__)
-  UI: links to authorities in the document editor
   `#244 <https://github.com/rero/rero-ils/pull/244>`__
   (`jma <https://github.com/jma>`__)
-  Circulation UI: Checkout possible according to circ policy
   `#243 <https://github.com/rero/rero-ils/pull/243>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  CIRCULATION: link from item details to circ UI
   `#241 <https://github.com/rero/rero-ils/pull/241>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  user interface: front page and header
   `#240 <https://github.com/rero/rero-ils/pull/240>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  RECORDS: can_delete fix for item and patron types
   `#239 <https://github.com/rero/rero-ils/pull/239>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  ES: person language mapping
   `#238 <https://github.com/rero/rero-ils/pull/238>`__
   (`rerowep <https://github.com/rerowep>`__)
-  UI: persons and documents public search view
   `#236 <https://github.com/rero/rero-ils/pull/236>`__
   (`jma <https://github.com/jma>`__)
-  user interface: menus structure
   `#228 <https://github.com/rero/rero-ils/pull/228>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  ES: loan mapping `#220 <https://github.com/rero/rero-ils/pull/220>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Circulation: Policy adapting for CIRC UI
   `#219 <https://github.com/rero/rero-ils/pull/219>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Circulation: nested mapping for cipo settings
   `#218 <https://github.com/rero/rero-ils/pull/218>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  UI: typeahead support for document search
   `#216 <https://github.com/rero/rero-ils/pull/216>`__
   (`jma <https://github.com/jma>`__)
-  Circulation Policies: Locate policy using item/patorn types pair
   `#214 <https://github.com/rero/rero-ils/pull/214>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  SERIALIZER: Fix resolve
   `#212 <https://github.com/rero/rero-ils/pull/212>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  user interface: translations
   `#211 <https://github.com/rero/rero-ils/pull/211>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Circulation: Circ policies backend
   `#210 <https://github.com/rero/rero-ils/pull/210>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  admin UI: fix and translations
   `#208 <https://github.com/rero/rero-ils/pull/208>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  repository: commit template
   `#207 <https://github.com/rero/rero-ils/pull/207>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  all: several fixes
   `#206 <https://github.com/rero/rero-ils/pull/206>`__
   (`jma <https://github.com/jma>`__)
-  DATA: $ref for mef persons
   `#205 <https://github.com/rero/rero-ils/pull/205>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Circulation: Circ policies backend
   `#204 <https://github.com/rero/rero-ils/pull/204>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  ADMIN UI: URL parameters and facets
   `#202 <https://github.com/rero/rero-ils/pull/202>`__
   (`jma <https://github.com/jma>`__)
-  Admin: Modal dialog
   `#201 <https://github.com/rero/rero-ils/pull/201>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  User interface: admin pages and jinja templates
   `#200 <https://github.com/rero/rero-ils/pull/200>`__
   (`jma <https://github.com/jma>`__)
-  DEPLOYMENT: docker
   `#198 <https://github.com/rero/rero-ils/pull/198>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Patron: Add communication channel
   `#197 <https://github.com/rero/rero-ils/pull/197>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  RECORDS: can_delete
   `#195 <https://github.com/rero/rero-ils/pull/195>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Angular lint `#194 <https://github.com/rero/rero-ils/pull/194>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  API: resolvers `#192 <https://github.com/rero/rero-ils/pull/192>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Admin: Circulation policy
   `#191 <https://github.com/rero/rero-ils/pull/191>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  ALL: $ref as link mecanism
   `#188 <https://github.com/rero/rero-ils/pull/188>`__
   (`jma <https://github.com/jma>`__)
-  Layout: refactoring
   `#186 <https://github.com/rero/rero-ils/pull/186>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Scripts: MEF harvesting
   `#185 <https://github.com/rero/rero-ils/pull/185>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Layout: admin page
   `#184 <https://github.com/rero/rero-ils/pull/184>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  VIEWS: fix $ref relations
   `#183 <https://github.com/rero/rero-ils/pull/183>`__
   (`jma <https://github.com/jma>`__)
-  Layout: document export view
   `#182 <https://github.com/rero/rero-ils/pull/182>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Layout: patron profile
   `#181 <https://github.com/rero/rero-ils/pull/181>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Layout: security pages, error pages, tombstones
   `#180 <https://github.com/rero/rero-ils/pull/180>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Layout: frontpage
   `#178 <https://github.com/rero/rero-ils/pull/178>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  FIXTURES: data importation with $ref.
   `#177 <https://github.com/rero/rero-ils/pull/177>`__
   (`jma <https://github.com/jma>`__)
-  Layout: person detailed view
   `#176 <https://github.com/rero/rero-ils/pull/176>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  API: jsonref introduction
   `#175 <https://github.com/rero/rero-ils/pull/175>`__
   (`jma <https://github.com/jma>`__)
-  Layout: search and brief views
   `#174 <https://github.com/rero/rero-ils/pull/174>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Layout: item detailed view
   `#172 <https://github.com/rero/rero-ils/pull/172>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Circulation policies settings
   `#171 <https://github.com/rero/rero-ils/pull/171>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  ADMIN: Fix translation
   `#166 <https://github.com/rero/rero-ils/pull/166>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  User: critical bug at menu initialization
   `#165 <https://github.com/rero/rero-ils/pull/165>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  ADMIN: Switch translation on the fly
   `#162 <https://github.com/rero/rero-ils/pull/162>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Admin interface: checkin/checkout implementation
   `#161 <https://github.com/rero/rero-ils/pull/161>`__
   (`jma <https://github.com/jma>`__)
-  Library translation
   `#160 <https://github.com/rero/rero-ils/pull/160>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Layout: documents detailed view
   `#159 <https://github.com/rero/rero-ils/pull/159>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Basic circulation policies
   `#158 <https://github.com/rero/rero-ils/pull/158>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  FIXTURE: libraries opening hours and exception dates
   `#157 <https://github.com/rero/rero-ils/pull/157>`__
   (`NicolasLabat <https://github.com/NicolasLabat>`__)
-  Library creation `#156 <https://github.com/rero/rero-ils/pull/156>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  API: library is open
   `#154 <https://github.com/rero/rero-ils/pull/154>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Maj circulation ui #724
   `#153 <https://github.com/rero/rero-ils/pull/153>`__
   (`jma <https://github.com/jma>`__)
-  Libraries: Form Validation
   `#152 <https://github.com/rero/rero-ils/pull/152>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Library: date exceptions
   `#151 <https://github.com/rero/rero-ils/pull/151>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Admin interface: menu refactoring
   `#150 <https://github.com/rero/rero-ils/pull/150>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  replace function `#149 <https://github.com/rero/rero-ils/pull/149>`__
   (`rerowep <https://github.com/rerowep>`__)
-  Circulation: configuration
   `#148 <https://github.com/rero/rero-ils/pull/148>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Libraries: add options opening_hours + new library editor
   `#147 <https://github.com/rero/rero-ils/pull/147>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Circulation: invenio-circulation integration
   `#146 <https://github.com/rero/rero-ils/pull/146>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Issue: Identify the two separate displays in the person detailed view
   `#141 <https://github.com/rero/rero-ils/pull/141>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  ISSUSES: patron parcode
   `#140 <https://github.com/rero/rero-ils/pull/140>`__
   (`rerowep <https://github.com/rerowep>`__)
-  User interface: menu list
   `#139 <https://github.com/rero/rero-ils/pull/139>`__
   (`rerowep <https://github.com/rerowep>`__)
-  admin ui: angular skeleton
   `#138 <https://github.com/rero/rero-ils/pull/138>`__
   (`jma <https://github.com/jma>`__)
-  Circulation: integration of invenio-circulation APIs
   `#136 <https://github.com/rero/rero-ils/pull/136>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Package: requests upgrade
   `#135 <https://github.com/rero/rero-ils/pull/135>`__
   (`BadrAly <https://github.com/BadrAly>`__)

`v0.1.0a20 <https://github.com/rero/rero-ils/tree/v0.1.0a20>`__ (2018-10-31)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.1.0a19...v0.1.0a20>`__

**Implemented enhancements:**

-  Circulation policy: Display the unit “days” units
   `#127 <https://github.com/rero/rero-ils/issues/127>`__

**Fixed bugs:**

-  Circulation policy form allows negative values
   `#125 <https://github.com/rero/rero-ils/issues/125>`__
-  api harvester size
   `#111 <https://github.com/rero/rero-ils/issues/111>`__
-  CSV export not working
   `#103 <https://github.com/rero/rero-ils/issues/103>`__

**Merged pull requests:**

-  User interface: header menu
   `#134 <https://github.com/rero/rero-ils/pull/134>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  circulation ui: member to library
   `#133 <https://github.com/rero/rero-ils/pull/133>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Member to library
   `#132 <https://github.com/rero/rero-ils/pull/132>`__
   (`rerowep <https://github.com/rerowep>`__)
-  frontend: translations
   `#130 <https://github.com/rero/rero-ils/pull/130>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Circulation policy: issues
   `#128 <https://github.com/rero/rero-ils/pull/128>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  Circulation: Policy configuration
   `#124 <https://github.com/rero/rero-ils/pull/124>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  frontend: cleaning
   `#122 <https://github.com/rero/rero-ils/pull/122>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  Item Types: Add resource
   `#116 <https://github.com/rero/rero-ils/pull/116>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Patron Types: Add resource
   `#115 <https://github.com/rero/rero-ils/pull/115>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  apiharvester: fix size
   `#113 <https://github.com/rero/rero-ils/pull/113>`__
   (`rerowep <https://github.com/rerowep>`__)

`v0.1.0a19 <https://github.com/rero/rero-ils/tree/v0.1.0a19>`__ (2018-10-11)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.1.0a18...v0.1.0a19>`__

**Implemented enhancements:**

-  Item status isn’t automatically updated in the item brief view
   `#20 <https://github.com/rero/rero-ils/issues/20>`__

**Fixed bugs:**

-  Jinja error after creating a document without identifiers (ISBN)
   `#109 <https://github.com/rero/rero-ils/issues/109>`__
-  Too many ``electronic\_location`` values for ebooks
   `#71 <https://github.com/rero/rero-ils/issues/71>`__

**Closed issues:**

-  Angularjs: Remove invenioSearchConfig (thumbnail.js)
   `#94 <https://github.com/rero/rero-ils/issues/94>`__
-  User roles display
   `#53 <https://github.com/rero/rero-ils/issues/53>`__
-  Uppercase in the facets
   `#44 <https://github.com/rero/rero-ils/issues/44>`__

**Merged pull requests:**

-  frontend: refactoring
   `#110 <https://github.com/rero/rero-ils/pull/110>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  User interface: translations
   `#108 <https://github.com/rero/rero-ils/pull/108>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  frontend: refactor layout
   `#107 <https://github.com/rero/rero-ils/pull/107>`__
   (`jma <https://github.com/jma>`__)
-  can delete `#105 <https://github.com/rero/rero-ils/pull/105>`__
   (`rerowep <https://github.com/rerowep>`__)
-  missing format_date_filter in items/view
   `#104 <https://github.com/rero/rero-ils/pull/104>`__
   (`rerowep <https://github.com/rerowep>`__)
-  git: gitignore extension
   `#102 <https://github.com/rero/rero-ils/pull/102>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  mef max harvest `#101 <https://github.com/rero/rero-ils/pull/101>`__
   (`rerowep <https://github.com/rerowep>`__)
-  oaiharvest port 8443
   `#100 <https://github.com/rero/rero-ils/pull/100>`__
   (`rerowep <https://github.com/rerowep>`__)
-  feat: Remove invenioSearchConfig and replace with invenioConfig
   `#99 <https://github.com/rero/rero-ils/pull/99>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  fixtures: users following personas templates
   `#98 <https://github.com/rero/rero-ils/pull/98>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  identifier for person link
   `#97 <https://github.com/rero/rero-ils/pull/97>`__
   (`rerowep <https://github.com/rerowep>`__)
-  feat: add source facet and source badge on briew view person
   `#96 <https://github.com/rero/rero-ils/pull/96>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  Person: Brief view `#95 <https://github.com/rero/rero-ils/pull/95>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  person detailed view
   `#90 <https://github.com/rero/rero-ils/pull/90>`__
   (`rerowep <https://github.com/rerowep>`__)
-  harvest mef `#85 <https://github.com/rero/rero-ils/pull/85>`__
   (`rerowep <https://github.com/rerowep>`__)
-  facets `#78 <https://github.com/rero/rero-ils/pull/78>`__
   (`rerowep <https://github.com/rerowep>`__)
-  fix: add exception on pipenv check
   `#77 <https://github.com/rero/rero-ils/pull/77>`__
   (`Garfield-fr <https://github.com/Garfield-fr>`__)
-  feat: add cover render services to brief and full view
   `#75 <https://github.com/rero/rero-ils/pull/75>`__
   (`jma <https://github.com/jma>`__)
-  documentation: installation and contributing
   `#74 <https://github.com/rero/rero-ils/pull/74>`__
   (`iGormilhit <https://github.com/iGormilhit>`__)
-  fix: link on assets with invenio collect
   `#73 <https://github.com/rero/rero-ils/pull/73>`__
   (`jma <https://github.com/jma>`__)
-  App data merge `#72 <https://github.com/rero/rero-ils/pull/72>`__
   (`jma <https://github.com/jma>`__)
-  search: AND by default
   `#68 <https://github.com/rero/rero-ils/pull/68>`__
   (`jma <https://github.com/jma>`__)

`v0.1.0a18 <https://github.com/rero/rero-ils/tree/v0.1.0a18>`__ (2018-08-23)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.1.0a17...v0.1.0a18>`__

**Merged pull requests:**

-  feat: ebooks harvesting
   `#69 <https://github.com/rero/rero-ils/pull/69>`__
   (`jma <https://github.com/jma>`__)

`v0.1.0a17 <https://github.com/rero/rero-ils/tree/v0.1.0a17>`__ (2018-08-20)
----------------------------------------------------------------------------

`Full
Changelog <https://github.com/rero/rero-ils/compare/v0.1.0a16...v0.1.0a17>`__

**Fixed bugs:**

-  Creation of item fails because of misspelled key label in the form
   options file `#61 <https://github.com/rero/rero-ils/issues/61>`__
-  Barcode not displayed on the request tab of the circulation UI
   `#59 <https://github.com/rero/rero-ils/issues/59>`__
-  Internal server error when adding a new item
   `#42 <https://github.com/rero/rero-ils/issues/42>`__

**Closed issues:**

-  Due date format should not display hours, minutes and seconds
   `#66 <https://github.com/rero/rero-ils/issues/66>`__
-  Translation of general status of documents
   `#60 <https://github.com/rero/rero-ils/issues/60>`__
-  The patron profile is displaying the loan start date instead of the
   loan due date `#57 <https://github.com/rero/rero-ils/issues/57>`__
-  Display item status on item detailed view
   `#46 <https://github.com/rero/rero-ils/issues/46>`__
-  Error not specified at patron creation
   `#9 <https://github.com/rero/rero-ils/issues/9>`__

**Merged pull requests:**

-  feat: new shuffled export
   `#67 <https://github.com/rero/rero-ils/pull/67>`__
   (`rerowep <https://github.com/rerowep>`__)
-  feat: add icons by doc type
   `#65 <https://github.com/rero/rero-ils/pull/65>`__
   (`BadrAly <https://github.com/BadrAly>`__)
-  add new document types
   `#63 <https://github.com/rero/rero-ils/pull/63>`__
   (`rerowep <https://github.com/rerowep>`__)

\* *This Changelog was automatically generated
by*\ `github_changelog_generator <https://github.com/github-changelog-generator/github-changelog-generator>`__
