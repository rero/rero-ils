# Changelog

## [v1.4.2](https://github.com/rero/rero-ils/tree/v1.4.2) (2021-07-14)

[Full Changelog](https://github.com/rero/rero-ils/compare/v1.4.1...v1.4.2)

**Fixed bugs:**

- It should not be possible to delete an item type with linked items [\#2159](https://github.com/rero/rero-ils/issues/2159)
- URL in e-mail sent to patrons with the wrong instance's URL [\#2151](https://github.com/rero/rero-ils/issues/2151)
- "To pick up until" in the notifications does not work [\#2140](https://github.com/rero/rero-ils/issues/2140)
- Notifications sent without object in the e-mail [\#2139](https://github.com/rero/rero-ils/issues/2139)
- Field `bookFormat` not correctly displayed in the editor [\#2088](https://github.com/rero/rero-ils/issues/2088)

**Closed issues:**

- "Your Libray" instead of "Your library" [\#2149](https://github.com/rero/rero-ils/issues/2149)

**Merged pull requests:**

- cli: fix create\_or\_update when pid is reserved [\#2163](https://github.com/rero/rero-ils/pull/2163) ([BadrAly](https://github.com/BadrAly))
- item types: deny deletion with temporary item type [\#2161](https://github.com/rero/rero-ils/pull/2161) ([Garfield-fr](https://github.com/Garfield-fr))
- notification: fix availability date [\#2158](https://github.com/rero/rero-ils/pull/2158) ([zannkukai](https://github.com/zannkukai))
- circulation: improve request to validate list [\#2157](https://github.com/rero/rero-ils/pull/2157) ([Garfield-fr](https://github.com/Garfield-fr))
- notifications: fix email subject [\#2156](https://github.com/rero/rero-ils/pull/2156) ([zannkukai](https://github.com/zannkukai))
- translation: fix "Your Libray" [\#2155](https://github.com/rero/rero-ils/pull/2155) ([zannkukai](https://github.com/zannkukai))
- patrons: display user PID in error message [\#2153](https://github.com/rero/rero-ils/pull/2153) ([rerowep](https://github.com/rerowep))

## [v1.4.1](https://github.com/rero/rero-ils/tree/v1.4.1) (2021-07-09)

[Full Changelog](https://github.com/rero/rero-ils/compare/v1.4.0...v1.4.1)

**Fixed bugs:**

- Duplicate item, or item list different in public and professional interface [\#2095](https://github.com/rero/rero-ils/issues/2095)

## [v1.4.0](https://github.com/rero/rero-ils/tree/v1.4.0) (2021-07-07)

[Full Changelog](https://github.com/rero/rero-ils/compare/v1.3.1...v1.4.0)

**Implemented enhancements:**

- ILL requests appear in the patron account even if they are closed or refused [\#2076](https://github.com/rero/rero-ils/issues/2076)
- Help: add a link to home page \(or ideally a table of content\) [\#1578](https://github.com/rero/rero-ils/issues/1578)
- Field `item.temporary\_location` is displayed in the public and professional interfaces [\#2038](https://github.com/rero/rero-ils/issues/2038)
- Display the queue position/number of requests \(prof. view/requests screen\) [\#2034](https://github.com/rero/rero-ils/issues/2034)
- ISBN are indexed in "keyword" mode but should be tokenised [\#2017](https://github.com/rero/rero-ils/issues/2017)
- documents: improve display of uniform resource locator [\#2071](https://github.com/rero/rero-ils/pull/2071) ([Garfield-fr](https://github.com/Garfield-fr))

**Fixed bugs:**

- Only one default circulation policy by organisation should be possible [\#2079](https://github.com/rero/rero-ils/issues/2079)
- The document field `relatedTo` is repeated three times in the list of field to be added, in the editor [\#2061](https://github.com/rero/rero-ils/issues/2061)
- Sub-field "Assigning agency" has the wrong title [\#2053](https://github.com/rero/rero-ils/issues/2053)
- Field `modeOfIssuance.subtype` sometimes not imported [\#1928](https://github.com/rero/rero-ils/issues/1928)
- Github actions test stops with an error related to test\_document\_boosting [\#1603](https://github.com/rero/rero-ils/issues/1603)
- Default filter by logged in organisation in document search does not work anymore [\#2130](https://github.com/rero/rero-ils/issues/2130)
- v1.4.0 RC bug list [\#2118](https://github.com/rero/rero-ils/issues/2118)
- No circulation transaction is anonymized [\#2055](https://github.com/rero/rero-ils/issues/2055)
- Issues on v1.3.0rc [\#2035](https://github.com/rero/rero-ils/issues/2035)
- The limit by overdue items is activated while the loans are not yet overdue [\#2014](https://github.com/rero/rero-ils/issues/2014)
- Circulation error for item migrated from Virtua [\#1983](https://github.com/rero/rero-ils/issues/1983)
- Item does not get the correct status after migrating Virtua loans [\#1974](https://github.com/rero/rero-ils/issues/1974)
- Missing activity data in the user DB [\#1961](https://github.com/rero/rero-ils/issues/1961)
- Problems on ilspilot, v1.2.0 [\#1959](https://github.com/rero/rero-ils/issues/1959)
- The "City" facet of the patron search relies on the wrong field [\#1949](https://github.com/rero/rero-ils/issues/1949)
- An item linked to a exhibition / course / collection is not displayed in the document detailed view [\#1942](https://github.com/rero/rero-ils/issues/1942)
- Adapt template fixtures to complete JSON schema [\#1905](https://github.com/rero/rero-ils/issues/1905)
- Unable to create circulation policies with different loan period for 2 different libraries [\#1859](https://github.com/rero/rero-ils/issues/1859)
- Interface does not display the right language [\#1391](https://github.com/rero/rero-ils/issues/1391)
- monitoring: fix ES duplicate display [\#2081](https://github.com/rero/rero-ils/pull/2081) ([rerowep](https://github.com/rerowep))
- public search: fix loading assets [\#2066](https://github.com/rero/rero-ils/pull/2066) ([Garfield-fr](https://github.com/Garfield-fr))
- circulation: fix `can\_extend` check method [\#2040](https://github.com/rero/rero-ils/pull/2040) ([zannkukai](https://github.com/zannkukai))

**Closed issues:**

- Prevent browser's suggestions when adding a new editor field [\#2037](https://github.com/rero/rero-ils/issues/2037)
- Only the first local field of each is imported from Virtua [\#1995](https://github.com/rero/rero-ils/issues/1995)
- Document encoding level should be required [\#1919](https://github.com/rero/rero-ils/issues/1919)

**Merged pull requests:**

- documents: adds missing item in book format [\#2115](https://github.com/rero/rero-ils/pull/2115) ([rerowep](https://github.com/rerowep))
- Implement stats for pricing [\#2112](https://github.com/rero/rero-ils/pull/2112) ([jma](https://github.com/jma))
- notifications: fix German availability template [\#2083](https://github.com/rero/rero-ils/pull/2083) ([rerowep](https://github.com/rerowep))
- circulation: allow only one default policy [\#2082](https://github.com/rero/rero-ils/pull/2082) ([zannkukai](https://github.com/zannkukai))
- tests: fix library `is\_open` unit test [\#2074](https://github.com/rero/rero-ils/pull/2074) ([zannkukai](https://github.com/zannkukai))
- cli: delete unused function [\#1976](https://github.com/rero/rero-ils/pull/1976) ([rerowep](https://github.com/rerowep))
- release: v1.4.1 [\#2137](https://github.com/rero/rero-ils/pull/2137) ([iGormilhit](https://github.com/iGormilhit))
- homepage: adaptation of the wallis homepage [\#2131](https://github.com/rero/rero-ils/pull/2131) ([Garfield-fr](https://github.com/Garfield-fr))
- users: fix CLI for user creation [\#2129](https://github.com/rero/rero-ils/pull/2129) ([rerowep](https://github.com/rerowep))
- release: v1.4.0 [\#2128](https://github.com/rero/rero-ils/pull/2128) ([iGormilhit](https://github.com/iGormilhit))
- translations: complete the v1.4.0 translations [\#2127](https://github.com/rero/rero-ils/pull/2127) ([iGormilhit](https://github.com/iGormilhit))
- operation logs: translate trigger actions [\#2125](https://github.com/rero/rero-ils/pull/2125) ([Garfield-fr](https://github.com/Garfield-fr))
- users: allow to save an user without email [\#2124](https://github.com/rero/rero-ils/pull/2124) ([zannkukai](https://github.com/zannkukai))
- documents: set `adminMetadata` as required field. [\#2120](https://github.com/rero/rero-ils/pull/2120) ([zannkukai](https://github.com/zannkukai))
- theme: fix missing ILL request menu [\#2119](https://github.com/rero/rero-ils/pull/2119) ([iGormilhit](https://github.com/iGormilhit))
- documents: improve BNF import [\#2117](https://github.com/rero/rero-ils/pull/2117) ([rerowep](https://github.com/rerowep))
- circulation: fix method for "is loan overdue" check [\#2114](https://github.com/rero/rero-ils/pull/2114) ([zannkukai](https://github.com/zannkukai))
- tests: fix unit test about loan overdue [\#2111](https://github.com/rero/rero-ils/pull/2111) ([zannkukai](https://github.com/zannkukai))
- documents: adapt the field list in quick access [\#2110](https://github.com/rero/rero-ils/pull/2110) ([Garfield-fr](https://github.com/Garfield-fr))
- items: add temporary location name by serializer [\#2105](https://github.com/rero/rero-ils/pull/2105) ([Garfield-fr](https://github.com/Garfield-fr))
- templates: remove `data` field from ES mapping [\#2100](https://github.com/rero/rero-ils/pull/2100) ([zannkukai](https://github.com/zannkukai))
- dependencies: fix celery version to = 5.0.5 [\#2099](https://github.com/rero/rero-ils/pull/2099) ([rerowep](https://github.com/rerowep))
- documentation: fix gh-actions labeler [\#2097](https://github.com/rero/rero-ils/pull/2097) ([iGormilhit](https://github.com/iGormilhit))
- patrons: fix problem with importing users [\#2094](https://github.com/rero/rero-ils/pull/2094) ([BadrAly](https://github.com/BadrAly))
- documents: remove a trailing dot in a title key [\#2093](https://github.com/rero/rero-ils/pull/2093) ([iGormilhit](https://github.com/iGormilhit))
- security: update dependencies [\#2091](https://github.com/rero/rero-ils/pull/2091) ([rerowep](https://github.com/rerowep))
- dojson: correct bookFormat transformation [\#2090](https://github.com/rero/rero-ils/pull/2090) ([rerowep](https://github.com/rerowep))
- patrons: allow to update user and patron records [\#2086](https://github.com/rero/rero-ils/pull/2086) ([BadrAly](https://github.com/BadrAly))
- document: fix multiple relatedTo [\#2085](https://github.com/rero/rero-ils/pull/2085) ([rerowep](https://github.com/rerowep))
- documents: reinforce availability robustness [\#2084](https://github.com/rero/rero-ils/pull/2084) ([rerowep](https://github.com/rerowep))
- fixtures: allow only one circulation policy [\#2078](https://github.com/rero/rero-ils/pull/2078) ([Garfield-fr](https://github.com/Garfield-fr))
- patrons: add email field on authenticate service [\#2077](https://github.com/rero/rero-ils/pull/2077) ([Garfield-fr](https://github.com/Garfield-fr))
- instance: install procps to monitor processes [\#2075](https://github.com/rero/rero-ils/pull/2075) ([BadrAly](https://github.com/BadrAly))
- circulation: add rank position information [\#2073](https://github.com/rero/rero-ils/pull/2073) ([zannkukai](https://github.com/zannkukai))
- homepage: implement organisation view [\#2070](https://github.com/rero/rero-ils/pull/2070) ([Garfield-fr](https://github.com/Garfield-fr))
- sip2: improve command line utilities [\#2069](https://github.com/rero/rero-ils/pull/2069) ([lauren-d](https://github.com/lauren-d))
- documentation: extend the gh-action labeler rules [\#2064](https://github.com/rero/rero-ils/pull/2064) ([iGormilhit](https://github.com/iGormilhit))
- documents: fix assigning agency title, description [\#2060](https://github.com/rero/rero-ils/pull/2060) ([iGormilhit](https://github.com/iGormilhit))
- search: add isbn text search [\#2057](https://github.com/rero/rero-ils/pull/2057) ([rerowep](https://github.com/rerowep))
- global: use JsonWriter [\#2047](https://github.com/rero/rero-ils/pull/2047) ([rerowep](https://github.com/rerowep))
- core: fix the wrong way to update a record [\#2046](https://github.com/rero/rero-ils/pull/2046) ([jma](https://github.com/jma))
- holdings: remove standard holdings with no items [\#2044](https://github.com/rero/rero-ils/pull/2044) ([BadrAly](https://github.com/BadrAly))
- patrons: tests multiple librarian roles [\#2030](https://github.com/rero/rero-ils/pull/2030) ([rerowep](https://github.com/rerowep))
- items: fix status according to migrated loans [\#2016](https://github.com/rero/rero-ils/pull/2016) ([BadrAly](https://github.com/BadrAly))

## [v1.3.1](https://github.com/rero/rero-ils/tree/v1.3.1) (2021-06-17)

[Full Changelog](https://github.com/rero/rero-ils/compare/v1.3.0...v1.3.1)

## [v1.3.0](https://github.com/rero/rero-ils/tree/v1.3.0) (2021-06-16)

[Full Changelog](https://github.com/rero/rero-ils/compare/v1.2.0...v1.3.0)

**Implemented enhancements:**

- Late issues: possibility to access directly the holdings [\#1808](https://github.com/rero/rero-ils/issues/1808)
- Add the target library in the checkin note "the item is in transit" [\#1798](https://github.com/rero/rero-ils/issues/1798)
- Allow to add an identifier to an author in a document [\#1793](https://github.com/rero/rero-ils/issues/1793)
- The request date should be displayed in the patron account of the professional interface [\#1778](https://github.com/rero/rero-ils/issues/1778)
- Minimum length of the item barcode [\#1485](https://github.com/rero/rero-ils/issues/1485)
- With the English interface, sometimes dates are displayed in the US format, which should be avoided at any cost [\#1469](https://github.com/rero/rero-ils/issues/1469)
- Document editor: some icons are on the right of the labels, some are on the right of the input field [\#1420](https://github.com/rero/rero-ils/issues/1420)
- Autocomplete does not work as expected with the second term of the search [\#1405](https://github.com/rero/rero-ils/issues/1405)
- Menus of the administration bar in the professional interface can be improved. [\#1375](https://github.com/rero/rero-ils/issues/1375)
- When the BNF server does not responds, display a clear message to the user. [\#1352](https://github.com/rero/rero-ils/issues/1352)
- Export of inventory lists should be impossible if there are too many items. [\#1329](https://github.com/rero/rero-ils/issues/1329)
- increase the log level for patron notifications [\#1241](https://github.com/rero/rero-ils/issues/1241)
- Hide the other organisation values and organisation count when one organisation is selected in the facet [\#962](https://github.com/rero/rero-ils/issues/962)
- Autocomplete doesn't work if your search contains diactrictics [\#1042](https://github.com/rero/rero-ils/issues/1042)
- Document view : navigation between public and professional interface [\#1040](https://github.com/rero/rero-ils/issues/1040)
- `ils.rero.ch` is renamed into `bib.rero.ch` [\#1896](https://github.com/rero/rero-ils/issues/1896)
- Toggle in each brief view to enable the standard query instead of the simple query [\#1824](https://github.com/rero/rero-ils/issues/1824)
- In a holdings, only active predictions should generate expected and late issues. [\#1807](https://github.com/rero/rero-ils/issues/1807)
- Find a better operation log implementation [\#1725](https://github.com/rero/rero-ils/issues/1725)
- Improve CSV export perfomance \(inventory list\) [\#1456](https://github.com/rero/rero-ils/issues/1456)
- Make the field `title.type` required for value "bf:Title" [\#1361](https://github.com/rero/rero-ils/issues/1361)
- circulation: enhance notifications in order to group emails sent to patrons [\#1236](https://github.com/rero/rero-ils/issues/1236)
- notifications: group notifications for each patron [\#1845](https://github.com/rero/rero-ils/pull/1845) ([rerowep](https://github.com/rerowep))
- items: improve response time for csv export [\#1842](https://github.com/rero/rero-ils/pull/1842) ([lauren-d](https://github.com/lauren-d))

**Fixed bugs:**

- No more warning on checkout page for a blocked patron [\#1964](https://github.com/rero/rero-ils/issues/1964)
- Impossible to save a document when created with a template [\#1926](https://github.com/rero/rero-ils/issues/1926)
- Template does not store the values of field `contentMediaCarrier` [\#1907](https://github.com/rero/rero-ils/issues/1907)
- Logged user without the patron role should not be able to edit the ILL request form [\#1895](https://github.com/rero/rero-ils/issues/1895)
- Identifier's qualifier, status and note should be displayed in professional interface [\#1846](https://github.com/rero/rero-ils/issues/1846)
- "Role" is not translated in the patron brief view. [\#1821](https://github.com/rero/rero-ils/issues/1821)
- Two confirmation messages when deleting the last item of a document [\#1817](https://github.com/rero/rero-ils/issues/1817)
- Toast message "dispute saved" is not completely translated [\#1814](https://github.com/rero/rero-ils/issues/1814)
- "Catalog" in the main menu is not translated [\#1812](https://github.com/rero/rero-ils/issues/1812)
- ILL requests: scope is always set to 'copy' [\#1671](https://github.com/rero/rero-ils/issues/1671)
- Translate the organisation detailed view of the professional interface [\#2036](https://github.com/rero/rero-ils/issues/2036)
- When editing an item of a document with lots of holdings and items, ES takes to much time [\#1943](https://github.com/rero/rero-ils/issues/1943)
- Toast message of circulation interface are not translated [\#1820](https://github.com/rero/rero-ils/issues/1820)
- Can't index an item template when field `item.type` exists [\#1776](https://github.com/rero/rero-ils/issues/1776)
- Notifications and fees don't respect the circulation policy settings [\#1741](https://github.com/rero/rero-ils/issues/1741)
- Missing Online access for bibliographic records with "Uniform Resource Locator"  [\#1722](https://github.com/rero/rero-ils/issues/1722)
- Some expected issues don't get the "late" status [\#1674](https://github.com/rero/rero-ils/issues/1674)
- Receive an issue: confusion between the status date and the date of receipt [\#1654](https://github.com/rero/rero-ils/issues/1654)
- template: allow to user `type` field into templates [\#1913](https://github.com/rero/rero-ils/pull/1913) ([zannkukai](https://github.com/zannkukai))
- patrons: correct city facet mapping [\#1990](https://github.com/rero/rero-ils/pull/1990) ([zannkukai](https://github.com/zannkukai))
- resources: improve organisation ref link validation [\#1973](https://github.com/rero/rero-ils/pull/1973) ([BadrAly](https://github.com/BadrAly))
- circulation: fix fees calculation [\#1955](https://github.com/rero/rero-ils/pull/1955) ([zannkukai](https://github.com/zannkukai))
- serials: fix issue.status\_date field update [\#1911](https://github.com/rero/rero-ils/pull/1911) ([zannkukai](https://github.com/zannkukai))
- circulation: restrict ILL request form to patron [\#1910](https://github.com/rero/rero-ils/pull/1910) ([zannkukai](https://github.com/zannkukai))

**Closed issues:**

- `encodingLevel` should be required in the document [\#1909](https://github.com/rero/rero-ils/issues/1909)
- ebooks: subjects are not unique [\#1731](https://github.com/rero/rero-ils/issues/1731)
- Label of the request list on item detailed view should be improved [\#1599](https://github.com/rero/rero-ils/issues/1599)
- Prediction pattern: disallow save function when the pattern is invalid [\#947](https://github.com/rero/rero-ils/issues/947)
- All budgets of same organisation are set to Active [\#828](https://github.com/rero/rero-ils/issues/828)
- Item with barcode 1002157781 is imported in the wrong location [\#2019](https://github.com/rero/rero-ils/issues/2019)
- The `price` is not correctly imported for items. [\#2007](https://github.com/rero/rero-ils/issues/2007)
- All fields from the bibliographic record to be imported in the item are missing [\#1997](https://github.com/rero/rero-ils/issues/1997)
- Intern note on document \(field 019\) is not correctly imported when MARC field is repeated [\#1996](https://github.com/rero/rero-ils/issues/1996)
- Country for users seems to be always set on Switzerland [\#1994](https://github.com/rero/rero-ils/issues/1994)
- User with a short last or first name are wrongly imported [\#1993](https://github.com/rero/rero-ils/issues/1993)
- 2 holdings created in RERO ILS instead of 1 present in Virtua [\#1989](https://github.com/rero/rero-ils/issues/1989)
- Some document records not imported from Virtua [\#1988](https://github.com/rero/rero-ils/issues/1988)
- The MARC field 555 is not considered in the import from Virtua [\#1987](https://github.com/rero/rero-ils/issues/1987)
- Local field for holdings \(incl. prediction\) not well formated [\#1985](https://github.com/rero/rero-ils/issues/1985)
- Items from 6 libraries affiliated to wrong libraries [\#1979](https://github.com/rero/rero-ils/issues/1979)
- The system doesn't use the today's date to compute overdue fees [\#1954](https://github.com/rero/rero-ils/issues/1954)
- The import of document field `issuance` is sometimes wrong [\#1951](https://github.com/rero/rero-ils/issues/1951)
- Wrong mapping for user secondary address and phone [\#1950](https://github.com/rero/rero-ils/issues/1950)
- `otherPhysicalFormat` should have as title "Also issued as" [\#1929](https://github.com/rero/rero-ils/issues/1929)
- Keep the ID of RERO authorities when IdRef or RERO-RAMEAU does not exist [\#1886](https://github.com/rero/rero-ils/issues/1886)
- Fields with links to authorities are adapted to be able to store identifiers [\#1885](https://github.com/rero/rero-ils/issues/1885)
- Harvested e-books should be marked as available [\#1872](https://github.com/rero/rero-ils/issues/1872)
- Title of the host document not indexed in the child document [\#1788](https://github.com/rero/rero-ils/issues/1788)
- Edit document fields `titlesProper`, `translatedFrom`, `abstracts` \(are newly implemented\) [\#1620](https://github.com/rero/rero-ils/issues/1620)
- Provision activity has no country for articles [\#1617](https://github.com/rero/rero-ils/issues/1617)

**Merged pull requests:**

- acquisitions: adds an account serializer [\#2028](https://github.com/rero/rero-ils/pull/2028) ([zannkukai](https://github.com/zannkukai))
- instance: change base URL [\#2021](https://github.com/rero/rero-ils/pull/2021) ([rerowep](https://github.com/rerowep))
- search: increase API limit [\#2010](https://github.com/rero/rero-ils/pull/2010) ([rerowep](https://github.com/rerowep))
- tests: fix external tests [\#1998](https://github.com/rero/rero-ils/pull/1998) ([rerowep](https://github.com/rerowep))
- translations: fix minor issues [\#1986](https://github.com/rero/rero-ils/pull/1986) ([rerowep](https://github.com/rerowep))
- Implements SRU [\#1962](https://github.com/rero/rero-ils/pull/1962) ([rerowep](https://github.com/rerowep))
- permissions: improve generation records permissions [\#1956](https://github.com/rero/rero-ils/pull/1956) ([lauren-d](https://github.com/lauren-d))
- acquisitions: create new extension [\#1948](https://github.com/rero/rero-ils/pull/1948) ([lauren-d](https://github.com/lauren-d))
- utils: add JSON writer [\#1941](https://github.com/rero/rero-ils/pull/1941) ([rerowep](https://github.com/rerowep))
- cli: fix wait\_empty\_tasks [\#1938](https://github.com/rero/rero-ils/pull/1938) ([rerowep](https://github.com/rerowep))
- merging 1.3.0 to dev [\#1903](https://github.com/rero/rero-ils/pull/1903) ([zannkukai](https://github.com/zannkukai))
- release v1.3.1 [\#2045](https://github.com/rero/rero-ils/pull/2045) ([iGormilhit](https://github.com/iGormilhit))
- search: restore ES settings in the template [\#2043](https://github.com/rero/rero-ils/pull/2043) ([rerowep](https://github.com/rerowep))
- release: v1.3.0 [\#2041](https://github.com/rero/rero-ils/pull/2041) ([iGormilhit](https://github.com/iGormilhit))
- sip2: implements selfcheck renewal [\#2039](https://github.com/rero/rero-ils/pull/2039) ([lauren-d](https://github.com/lauren-d))
- orders: remove the total amount from the DB [\#2032](https://github.com/rero/rero-ils/pull/2032) ([jma](https://github.com/jma))
-  documents: complete the data conversion [\#2031](https://github.com/rero/rero-ils/pull/2031) ([reropag](https://github.com/reropag))
- sip2: use item barcode instead item pid [\#2029](https://github.com/rero/rero-ils/pull/2029) ([lauren-d](https://github.com/lauren-d))
- document: make document `mainTitle` unique [\#2024](https://github.com/rero/rero-ils/pull/2024) ([zannkukai](https://github.com/zannkukai))
- translations: translate v1.3.0 [\#2023](https://github.com/rero/rero-ils/pull/2023) ([iGormilhit](https://github.com/iGormilhit))
- authentication: implement OAuth server [\#2022](https://github.com/rero/rero-ils/pull/2022) ([sebastiendeleze](https://github.com/sebastiendeleze))
- Implement history loan logs [\#2018](https://github.com/rero/rero-ils/pull/2018) ([jma](https://github.com/jma))
- circulation: masked item are not available [\#2015](https://github.com/rero/rero-ils/pull/2015) ([zannkukai](https://github.com/zannkukai))
- holdings: add item counts [\#2012](https://github.com/rero/rero-ils/pull/2012) ([jma](https://github.com/jma))
- users: release constraint on the first & last name [\#2009](https://github.com/rero/rero-ils/pull/2009) ([iGormilhit](https://github.com/iGormilhit))
- patrons: allow external service to authenticate users [\#2006](https://github.com/rero/rero-ils/pull/2006) ([Garfield-fr](https://github.com/Garfield-fr))
- docker: change value for restart parameter [\#2005](https://github.com/rero/rero-ils/pull/2005) ([Garfield-fr](https://github.com/Garfield-fr))
- tests: script to test a lot of update [\#2003](https://github.com/rero/rero-ils/pull/2003) ([sebastiendeleze](https://github.com/sebastiendeleze))
- items: add new temporary\_location field [\#2002](https://github.com/rero/rero-ils/pull/2002) ([BadrAly](https://github.com/BadrAly))
- user profiles: translate username description [\#2001](https://github.com/rero/rero-ils/pull/2001) ([iGormilhit](https://github.com/iGormilhit))
- resources: speed up the indexing [\#1999](https://github.com/rero/rero-ils/pull/1999) ([jma](https://github.com/jma))
- documents: fix `encodingLevel` admin metadata [\#1991](https://github.com/rero/rero-ils/pull/1991) ([zannkukai](https://github.com/zannkukai))
- patron type: add `code` field [\#1980](https://github.com/rero/rero-ils/pull/1980) ([sebastiendeleze](https://github.com/sebastiendeleze))
- data: set local\_fields field minLength to 1 char [\#1972](https://github.com/rero/rero-ils/pull/1972) ([BadrAly](https://github.com/BadrAly))
- documentation: extend the gh-actions labeler rules [\#1969](https://github.com/rero/rero-ils/pull/1969) ([iGormilhit](https://github.com/iGormilhit))
- wiki: improve flask-wiki integration [\#1968](https://github.com/rero/rero-ils/pull/1968) ([iGormilhit](https://github.com/iGormilhit))
- translations: fix minor issues [\#1963](https://github.com/rero/rero-ils/pull/1963) ([rerowep](https://github.com/rerowep))
- fixtures: adapt templates to the complete document schema [\#1960](https://github.com/rero/rero-ils/pull/1960) ([rerowep](https://github.com/rerowep))
- fix: empty list in function parameters [\#1953](https://github.com/rero/rero-ils/pull/1953) ([rerowep](https://github.com/rerowep))
- api: fix delete in api and dojson issuance [\#1940](https://github.com/rero/rero-ils/pull/1940) ([rerowep](https://github.com/rerowep))
- Remove legacy documents fields [\#1935](https://github.com/rero/rero-ils/pull/1935) ([rerowep](https://github.com/rerowep))
- update gh labeler [\#1934](https://github.com/rero/rero-ils/pull/1934) ([iGormilhit](https://github.com/iGormilhit))
- documents: fix elasticsearch mapping [\#1933](https://github.com/rero/rero-ils/pull/1933) ([lauren-d](https://github.com/lauren-d))
- documents: update the publication statement text [\#1931](https://github.com/rero/rero-ils/pull/1931) ([rerowep](https://github.com/rerowep))
- tests: remove manifest fix [\#1930](https://github.com/rero/rero-ils/pull/1930) ([rerowep](https://github.com/rerowep))
- tests: copy manifest.json to fix tests [\#1927](https://github.com/rero/rero-ils/pull/1927) ([rerowep](https://github.com/rerowep))
- search: add missing mappings [\#1925](https://github.com/rero/rero-ils/pull/1925) ([rerowep](https://github.com/rerowep))
- tests: constrain the Flask version to fix tests [\#1923](https://github.com/rero/rero-ils/pull/1923) ([iGormilhit](https://github.com/iGormilhit))
- documents: store source of authority identifiers [\#1917](https://github.com/rero/rero-ils/pull/1917) ([rerowep](https://github.com/rerowep))
- notifications: adds library notifications [\#1914](https://github.com/rero/rero-ils/pull/1914) ([Garfield-fr](https://github.com/Garfield-fr))
- resources: improve indexing performance & ES mapping [\#1912](https://github.com/rero/rero-ils/pull/1912) ([zannkukai](https://github.com/zannkukai))
- readme: add translation info and update copyright [\#1891](https://github.com/rero/rero-ils/pull/1891) ([mmo](https://github.com/mmo))
- cli: fix several things [\#1881](https://github.com/rero/rero-ils/pull/1881) ([rerowep](https://github.com/rerowep))
- documents: improve online access information [\#1844](https://github.com/rero/rero-ils/pull/1844) ([Garfield-fr](https://github.com/Garfield-fr))
- search: improve control of the simple parameter [\#1843](https://github.com/rero/rero-ils/pull/1843) ([Garfield-fr](https://github.com/Garfield-fr))
- metadata: import, export, create csv data files [\#1710](https://github.com/rero/rero-ils/pull/1710) ([rerowep](https://github.com/rerowep))

## [v1.2.0](https://github.com/rero/rero-ils/tree/v1.2.0) (2021-05-06)

[Full Changelog](https://github.com/rero/rero-ils/compare/v1.1.0...v1.2.0)

**Implemented enhancements:**

- Singular/plural should be taken into consideration for some nouns [\#1805](https://github.com/rero/rero-ils/issues/1805)
- Serial issue: add "expected" in the item status [\#1796](https://github.com/rero/rero-ils/issues/1796)
- The acquisition accounts should be alphabetically sorted [\#1781](https://github.com/rero/rero-ils/issues/1781)
- Confirmation before submitting an ILL request [\#1771](https://github.com/rero/rero-ils/issues/1771)
- Holdings : change the name of "Available collection" and "Supplementary content" [\#1769](https://github.com/rero/rero-ils/issues/1769)
- Check for duplicated identifier \(ISBN/ISSN\) in the document editor [\#1664](https://github.com/rero/rero-ils/issues/1664)
- Collection title and description should be indexed in the document index [\#1583](https://github.com/rero/rero-ils/issues/1583)
- A librarian shouldn't be able to resolve fees of item not belonging to the login location [\#1533](https://github.com/rero/rero-ils/issues/1533)
- A user has an account in multiple organisations. [\#1460](https://github.com/rero/rero-ils/issues/1460)
- documents: improve search result boosting [\#1863](https://github.com/rero/rero-ils/pull/1863) ([rerowep](https://github.com/rerowep))
- users: validate records through a CLI [\#1878](https://github.com/rero/rero-ils/pull/1878) ([rerowep](https://github.com/rerowep))

**Fixed bugs:**

- It is impossible to create a circulation policy with overdue fees [\#1848](https://github.com/rero/rero-ils/issues/1848)
- User with patron and librarian roles can't view request info in item detail view [\#1839](https://github.com/rero/rero-ils/issues/1839)
- Delete a vendor is possible even if holdings are linked to it [\#1822](https://github.com/rero/rero-ils/issues/1822)
- The identifier qualification / qualifier is not imported from MARC [\#1799](https://github.com/rero/rero-ils/issues/1799)
- Fees: transaction history not sorted by date/time [\#1766](https://github.com/rero/rero-ils/issues/1766)
- Local fields shouldn't be displayed in the 'import from the web' document view [\#1564](https://github.com/rero/rero-ils/issues/1564)
- Bug list for the v1.2.0 RC [\#1873](https://github.com/rero/rero-ils/issues/1873)
- Position in the request waiting queue is not displayed anymore to the patron [\#1851](https://github.com/rero/rero-ils/issues/1851)
- "My Account" menu doesn't appear for user with role librarian [\#1837](https://github.com/rero/rero-ils/issues/1837)
- Keep history settings enabled but not taken into account [\#1804](https://github.com/rero/rero-ils/issues/1804)
- Some Virtua vendors are missing in RERO ILS [\#1791](https://github.com/rero/rero-ils/issues/1791)
- Sort by due date not applied by default in the circulation interface [\#1703](https://github.com/rero/rero-ils/issues/1703)
- In the pro and public patron account, loans are marked as overdue too late. [\#1389](https://github.com/rero/rero-ils/issues/1389)
- add icon\_docmaintype\_children.svg [\#1831](https://github.com/rero/rero-ils/pull/1831) ([rerowep](https://github.com/rerowep))
- fix Exception [\#1826](https://github.com/rero/rero-ils/pull/1826) ([rerowep](https://github.com/rerowep))
- tests: fix `test\_documents\_import\_bnf\_ean` for pycodestyle [\#1809](https://github.com/rero/rero-ils/pull/1809) ([lauren-d](https://github.com/lauren-d))
- contributions: restore missing Jinja templates [\#1874](https://github.com/rero/rero-ils/pull/1874) ([jma](https://github.com/jma))
- documents: fix json schema for identifier [\#1862](https://github.com/rero/rero-ils/pull/1862) ([rerowep](https://github.com/rerowep))
- fees: fix creation of not overdue fee [\#1861](https://github.com/rero/rero-ils/pull/1861) ([zannkukai](https://github.com/zannkukai))
- search: fix circulation search factory [\#1840](https://github.com/rero/rero-ils/pull/1840) ([lauren-d](https://github.com/lauren-d))

**Closed issues:**

- Rename in the item field "Enumeration and chronology" into "Unit" [\#1830](https://github.com/rero/rero-ils/issues/1830)
- Description of field `checkout\_duration` is not correct in the circulation policy editor [\#1813](https://github.com/rero/rero-ils/issues/1813)
- The patron `local\_code` should be repetitive [\#1806](https://github.com/rero/rero-ils/issues/1806)
- Document model : add usageAndAccessPolicy [\#1757](https://github.com/rero/rero-ils/issues/1757)
- In the brief view, the word "Organisation" is changed in the tab and in the facet. [\#1728](https://github.com/rero/rero-ils/issues/1728)
- "Collection" is renamed into "exhibition/course" [\#1672](https://github.com/rero/rero-ils/issues/1672)
- The availability of a holdings of type "serial" with no items should not be "no items received" [\#1586](https://github.com/rero/rero-ils/issues/1586)
- Collection identifier should be optional [\#1584](https://github.com/rero/rero-ils/issues/1584)
- Prevent the enter key to submit the form in some fields that may be filled though a scanning device [\#1421](https://github.com/rero/rero-ils/issues/1421)

**Merged pull requests:**

- Us 2034 multiple patron [\#1858](https://github.com/rero/rero-ils/pull/1858) ([jma](https://github.com/jma))
- documents: improve editor [\#1832](https://github.com/rero/rero-ils/pull/1832) ([Garfield-fr](https://github.com/Garfield-fr))
- security: update dependencies [\#1823](https://github.com/rero/rero-ils/pull/1823) ([jma](https://github.com/jma))
- collections: rename into "Exhibition/course" [\#1815](https://github.com/rero/rero-ils/pull/1815) ([Garfield-fr](https://github.com/Garfield-fr))
- US2014 SIP2 implementation at RERO [\#1810](https://github.com/rero/rero-ils/pull/1810) ([lauren-d](https://github.com/lauren-d))
- circulation category: negative availability [\#1803](https://github.com/rero/rero-ils/pull/1803) ([zannkukai](https://github.com/zannkukai))
- records: fix bug when reading the input file of pids [\#1785](https://github.com/rero/rero-ils/pull/1785) ([BadrAly](https://github.com/BadrAly))
- transaction: add library for patron transactions [\#1773](https://github.com/rero/rero-ils/pull/1773) ([jma](https://github.com/jma))
- editor: prevent the enter key to submit the form [\#1772](https://github.com/rero/rero-ils/pull/1772) ([jma](https://github.com/jma))
- test: fix `test\_item\_loans\_elements` unit test. [\#1768](https://github.com/rero/rero-ils/pull/1768) ([zannkukai](https://github.com/zannkukai))
- Document: index collection title and description. [\#1764](https://github.com/rero/rero-ils/pull/1764) ([zannkukai](https://github.com/zannkukai))
- tests: mocked BNF tests [\#1700](https://github.com/rero/rero-ils/pull/1700) ([rerowep](https://github.com/rerowep))
- documents: complete the JSON schema [\#1693](https://github.com/rero/rero-ils/pull/1693) ([rerowep](https://github.com/rerowep))
- release: v1.2.0 [\#1892](https://github.com/rero/rero-ils/pull/1892) ([iGormilhit](https://github.com/iGormilhit))
- translations: translate further v1.2.0 [\#1890](https://github.com/rero/rero-ils/pull/1890) ([iGormilhit](https://github.com/iGormilhit))
- selfcheck: fix checkin/checkout action [\#1889](https://github.com/rero/rero-ils/pull/1889) ([lauren-d](https://github.com/lauren-d))
- users: set local\_code field minLength to 1 [\#1880](https://github.com/rero/rero-ils/pull/1880) ([BadrAly](https://github.com/BadrAly))
- translations: translate v1.2.0 [\#1870](https://github.com/rero/rero-ils/pull/1870) ([iGormilhit](https://github.com/iGormilhit))
- documents: update subject display [\#1860](https://github.com/rero/rero-ils/pull/1860) ([Garfield-fr](https://github.com/Garfield-fr))
- circulation: load legacy transactions [\#1856](https://github.com/rero/rero-ils/pull/1856) ([BadrAly](https://github.com/BadrAly))
- data: allow to update existing records [\#1841](https://github.com/rero/rero-ils/pull/1841) ([BadrAly](https://github.com/BadrAly))
- translations: fix the extraction process [\#1836](https://github.com/rero/rero-ils/pull/1836) ([iGormilhit](https://github.com/iGormilhit))
- documents: complete the data conversion [\#1835](https://github.com/rero/rero-ils/pull/1835) ([reropag](https://github.com/reropag))
- tests: restore pycodestyle check [\#1784](https://github.com/rero/rero-ils/pull/1784) ([rerowep](https://github.com/rerowep))

## [v1.1.0](https://github.com/rero/rero-ils/tree/v1.1.0) (2021-03-29)

[Full Changelog](https://github.com/rero/rero-ils/compare/v1.0.1...v1.1.0)

**Implemented enhancements:**

- The expected issues are difficult to read, the grey is to light. [\#1717](https://github.com/rero/rero-ils/issues/1717)
- Patron barcodes should be imported into the username field [\#1670](https://github.com/rero/rero-ils/issues/1670)
- Sort option for items within a holdings [\#1625](https://github.com/rero/rero-ils/issues/1625)
- Fields name and birth date should not be editable by a user/patron [\#1318](https://github.com/rero/rero-ils/issues/1318)
- libraries: closed date API [\#1730](https://github.com/rero/rero-ils/pull/1730) ([zannkukai](https://github.com/zannkukai))

**Fixed bugs:**

- E-books are not searchable in the organisation views of ilspilot [\#1780](https://github.com/rero/rero-ils/issues/1780)
- Migrated bibs should have the correct URL format [\#1737](https://github.com/rero/rero-ils/issues/1737)
- Loan end date is false  [\#1735](https://github.com/rero/rero-ils/issues/1735)
- Search spinner in progress even after search is complete [\#1689](https://github.com/rero/rero-ils/issues/1689)
- The affiliation library disappears in some cases in the patron editor [\#1634](https://github.com/rero/rero-ils/issues/1634)
- Checkout at fixed date doesn't allow to choose the current date [\#1574](https://github.com/rero/rero-ils/issues/1574)
- No feedback is given to the user if the email is not confirmed [\#1490](https://github.com/rero/rero-ils/issues/1490)
- Wrong display of some fields on the circulation interface [\#1447](https://github.com/rero/rero-ils/issues/1447)
- Document main title is not displayed with all subtitles [\#1745](https://github.com/rero/rero-ils/issues/1745)
- Fixed date: closed date with repetition not taken into account [\#1734](https://github.com/rero/rero-ils/issues/1734)
- Request - item detail view: request section should be always displayed [\#1715](https://github.com/rero/rero-ils/issues/1715)
- ILL request detail view: error message if the librarian has also the role patron. [\#1709](https://github.com/rero/rero-ils/issues/1709)
- ILL request form: patron wrongly displayed [\#1708](https://github.com/rero/rero-ils/issues/1708)
- Add a second filter to the organisation facet filter has no effect [\#1684](https://github.com/rero/rero-ils/issues/1684)
- In the professional patron account, the counter of the "Pending" tab is not updated after a checkout [\#1579](https://github.com/rero/rero-ils/issues/1579)
- Impossible to save a circulation policy if only one toggle is enabled [\#1573](https://github.com/rero/rero-ils/issues/1573)
- Creating a patron with a username and an email corresponding to two different invenio user cause unpredictable errors [\#1467](https://github.com/rero/rero-ils/issues/1467)

**Closed issues:**

- Document model : add the type bf:Lccn to identifiers [\#1756](https://github.com/rero/rero-ils/issues/1756)
- Remove codes with a colon from the document JSON schema [\#1619](https://github.com/rero/rero-ils/issues/1619)
- Place should be required in document field "Provision activity" [\#1739](https://github.com/rero/rero-ils/issues/1739)
- Improve response time for circulation operations [\#1600](https://github.com/rero/rero-ils/issues/1600)
- circulation: block checkout/renew/request when patron expiration date is reached [\#1495](https://github.com/rero/rero-ils/issues/1495)
- Send notification "availability" some time after the item is checked in [\#913](https://github.com/rero/rero-ils/issues/913)

**Merged pull requests:**

- menu: display "my account" only for a patron [\#1792](https://github.com/rero/rero-ils/pull/1792) ([Garfield-fr](https://github.com/Garfield-fr))
- release: v1.1.0 [\#1787](https://github.com/rero/rero-ils/pull/1787) ([jma](https://github.com/jma))
- document: add 'bf:Lccn' as identifier type [\#1767](https://github.com/rero/rero-ils/pull/1767) ([zannkukai](https://github.com/zannkukai))
- document: place field required for provision activity [\#1762](https://github.com/rero/rero-ils/pull/1762) ([zannkukai](https://github.com/zannkukai))
- library: correct exception dates behavior. [\#1761](https://github.com/rero/rero-ils/pull/1761) ([zannkukai](https://github.com/zannkukai))
- test: fix break test. [\#1755](https://github.com/rero/rero-ils/pull/1755) ([zannkukai](https://github.com/zannkukai))
- Us cipo reminders fees [\#1753](https://github.com/rero/rero-ils/pull/1753) ([zannkukai](https://github.com/zannkukai))
- documents: fix coverart [\#1750](https://github.com/rero/rero-ils/pull/1750) ([rerowep](https://github.com/rerowep))
- security: update dependencies [\#1748](https://github.com/rero/rero-ils/pull/1748) ([BadrAly](https://github.com/BadrAly))
- US1889 patron edit personnal data [\#1742](https://github.com/rero/rero-ils/pull/1742) ([jma](https://github.com/jma))
- circulation: improve response time for circulation operations [\#1668](https://github.com/rero/rero-ils/pull/1668) ([rerowep](https://github.com/rerowep))
- US1906 complete item model [\#1777](https://github.com/rero/rero-ils/pull/1777) ([BadrAly](https://github.com/BadrAly))
- permissions: correct caching problems [\#1765](https://github.com/rero/rero-ils/pull/1765) ([zannkukai](https://github.com/zannkukai))
- document: resolve the processing of the title field [\#1760](https://github.com/rero/rero-ils/pull/1760) ([Garfield-fr](https://github.com/Garfield-fr))
- user profile: reorganize menu [\#1759](https://github.com/rero/rero-ils/pull/1759) ([Garfield-fr](https://github.com/Garfield-fr))
- circulation: block operations for expired patron [\#1743](https://github.com/rero/rero-ils/pull/1743) ([zannkukai](https://github.com/zannkukai))
- circulation: Fix in-house checkout [\#1736](https://github.com/rero/rero-ils/pull/1736) ([zannkukai](https://github.com/zannkukai))
- circulation: update invenio-circulation to v1.0.0a30 [\#1733](https://github.com/rero/rero-ils/pull/1733) ([BadrAly](https://github.com/BadrAly))
- holdings: allow optional fields for electronic holdings [\#1723](https://github.com/rero/rero-ils/pull/1723) ([lauren-d](https://github.com/lauren-d))
- patrons: update data for the new patron profile [\#1721](https://github.com/rero/rero-ils/pull/1721) ([Garfield-fr](https://github.com/Garfield-fr))
- ILL request: fix permissions [\#1714](https://github.com/rero/rero-ils/pull/1714) ([zannkukai](https://github.com/zannkukai))
- libraries: add notification settings in library definition [\#1691](https://github.com/rero/rero-ils/pull/1691) ([AoNoOokami](https://github.com/AoNoOokami))
- public ui: better document type facet [\#1680](https://github.com/rero/rero-ils/pull/1680) ([rerowep](https://github.com/rerowep))

## [v1.0.1](https://github.com/rero/rero-ils/tree/v1.0.1) (2021-03-02)

[Full Changelog](https://github.com/rero/rero-ils/compare/v1.0.0...v1.0.1)

**Implemented enhancements:**

- Add a validation for field `electronicLocator.url` [\#1426](https://github.com/rero/rero-ils/issues/1426)
- Display a hyper text link when adding a $ref link to another resource in the editor [\#1425](https://github.com/rero/rero-ils/issues/1425)
- Agent is difficult to understand in the provision activity of the document editor [\#1423](https://github.com/rero/rero-ils/issues/1423)
- Restrict pick-up in the location editor should be possible only if requests are enabled. [\#1366](https://github.com/rero/rero-ils/issues/1366)
- Display optional repetitive field only once [\#1604](https://github.com/rero/rero-ils/issues/1604)
- Add authority link to contributor suggestions in the document editor [\#1598](https://github.com/rero/rero-ils/issues/1598)
- Display `partOf` on the brief views [\#1596](https://github.com/rero/rero-ils/issues/1596)

**Fixed bugs:**

- A user get an internal servor error as he wants to save changes in his profile [\#1724](https://github.com/rero/rero-ils/issues/1724)
- Cannot add new fields to a duplicate bibliographic record [\#1601](https://github.com/rero/rero-ils/issues/1601)
- Document subtype "audio book" is missing. [\#1712](https://github.com/rero/rero-ils/issues/1712)
- serials: enumeration and chronology field is incorrect in the slow issue receive [\#1696](https://github.com/rero/rero-ils/issues/1696)
- items attached to holdings are not shown in the organisational public view [\#1688](https://github.com/rero/rero-ils/issues/1688)
- Missing string translation on holdings/items screen [\#1687](https://github.com/rero/rero-ils/issues/1687)
- Admin menu entries cannot be translated. [\#1627](https://github.com/rero/rero-ils/issues/1627)

**Security fixes:**

- dependencies: fix security issues [\#1732](https://github.com/rero/rero-ils/pull/1732) ([jma](https://github.com/jma))

**Closed issues:**

- An issue with status "deleted" is displayed in the public interface [\#1719](https://github.com/rero/rero-ils/issues/1719)
- Only received issues are displayed on the document detailed view of the public interface [\#1661](https://github.com/rero/rero-ils/issues/1661)
- Holdings of serial type should be displayed on document detailed view of all kind of document type \(public interface\) [\#1660](https://github.com/rero/rero-ils/issues/1660)
- Contributor autocomplete in document editor does not ignore diacritics [\#1462](https://github.com/rero/rero-ils/issues/1462)

**Merged pull requests:**

- release: v1.0.1 [\#1738](https://github.com/rero/rero-ils/pull/1738) ([iGormilhit](https://github.com/iGormilhit))
- documents: fix bug when generating the big and small items [\#1727](https://github.com/rero/rero-ils/pull/1727) ([BadrAly](https://github.com/BadrAly))
- items: fix holding update when receiving an issue [\#1713](https://github.com/rero/rero-ils/pull/1713) ([zannkukai](https://github.com/zannkukai))
- query: search filter on item [\#1699](https://github.com/rero/rero-ils/pull/1699) ([Garfield-fr](https://github.com/Garfield-fr))
- various: fix and improve several things [\#1698](https://github.com/rero/rero-ils/pull/1698) ([rerowep](https://github.com/rerowep))
- monitoring: configure ElasticSearch monitoring [\#1694](https://github.com/rero/rero-ils/pull/1694) ([rerowep](https://github.com/rerowep))
- tests: fix cypress tests [\#1685](https://github.com/rero/rero-ils/pull/1685) ([AoNoOokami](https://github.com/AoNoOokami))
- operation logs: migrate legacy operation logs [\#1677](https://github.com/rero/rero-ils/pull/1677) ([BadrAly](https://github.com/BadrAly))
- users: add user info API [\#1656](https://github.com/rero/rero-ils/pull/1656) ([jma](https://github.com/jma))
- editor: adapt JSON schema form options [\#1647](https://github.com/rero/rero-ils/pull/1647) ([jma](https://github.com/jma))
- test: add cypress tests for document creation [\#1595](https://github.com/rero/rero-ils/pull/1595) ([AoNoOokami](https://github.com/AoNoOokami))

## [v1.0.0](https://github.com/rero/rero-ils/tree/v1.0.0) (2021-02-09)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.15.0...v1.0.0)

**Implemented enhancements:**

- Index both ISBN 10 and 13 format in the document index [\#1486](https://github.com/rero/rero-ils/issues/1486)
- Serial holdings should be allowed on any document types [\#1612](https://github.com/rero/rero-ils/issues/1612)
- "Label" should be renamed into "Unit" in the professional document detailed view [\#1577](https://github.com/rero/rero-ils/issues/1577)
- The "Login \(to see request options\)" button should be more visible on public document detailed view. [\#1473](https://github.com/rero/rero-ils/issues/1473)
- Performance issue when loading and displaying documents with many items in the public interface [\#1401](https://github.com/rero/rero-ils/issues/1401)
- Holdings should be grouped by libraries [\#1399](https://github.com/rero/rero-ils/issues/1399)
- Two result counts are not understandable by end users [\#1395](https://github.com/rero/rero-ils/issues/1395)
- The tab displayed when opening a detailed view seems to be random. [\#1394](https://github.com/rero/rero-ils/issues/1394)
- Reset password e-mails are too terse and untranslated [\#1387](https://github.com/rero/rero-ils/issues/1387)
- The issue call number should be generated according to the holdings call number. [\#1288](https://github.com/rero/rero-ils/issues/1288)
- Image thumbnails for documents should be displayed in pro interface [\#1188](https://github.com/rero/rero-ils/issues/1188)
- notification: improve password reset notifications [\#1589](https://github.com/rero/rero-ils/pull/1589) ([AoNoOokami](https://github.com/AoNoOokami))
- documents: group holdings by libraries [\#1541](https://github.com/rero/rero-ils/pull/1541) ([Garfield-fr](https://github.com/Garfield-fr))

**Fixed bugs:**

- 2nd-level values of hierarchical facets are not always sorted according to their parent value [\#1697](https://github.com/rero/rero-ils/issues/1697)
- The error message in the prediction preview is not for end users. [\#1290](https://github.com/rero/rero-ils/issues/1290)
- Button 'login \(to see request options\)' has a wrong URL [\#1639](https://github.com/rero/rero-ils/issues/1639)
- Help link on ilspilot refers to ils.test [\#1575](https://github.com/rero/rero-ils/issues/1575)
- Contribution aggregations are missing on the "import from the web" professional interface [\#1571](https://github.com/rero/rero-ils/issues/1571)
- Notification history not in chronological order in the circulation interface [\#1549](https://github.com/rero/rero-ils/issues/1549)
- The search of the public interface does not adapt its suggestions to the browser locale [\#1509](https://github.com/rero/rero-ils/issues/1509)
- Cannot save a prediction pattern for an existing holding [\#1471](https://github.com/rero/rero-ils/issues/1471)
- CHECKOUT\_4 or CHECKOUT\_5 does not work as expected. [\#1379](https://github.com/rero/rero-ils/issues/1379)
- In the pro patron account, the message for item in transit is not translated. [\#1376](https://github.com/rero/rero-ils/issues/1376)
- Unable to use dynamic date with a "+" character for the new acquisition URL creation [\#1237](https://github.com/rero/rero-ils/issues/1237)
- There is no information on the item when a checkin without action is performed [\#1168](https://github.com/rero/rero-ils/issues/1168)
- holdings: fix several bugs related to version 1.0.0 [\#1681](https://github.com/rero/rero-ils/pull/1681) ([BadrAly](https://github.com/BadrAly))
- public ui: fix standard coverart in detailed view [\#1678](https://github.com/rero/rero-ils/pull/1678) ([rerowep](https://github.com/rerowep))
- public ui: fix login button on holdings section [\#1663](https://github.com/rero/rero-ils/pull/1663) ([rerowep](https://github.com/rerowep))
- test: fix test in house [\#1644](https://github.com/rero/rero-ils/pull/1644) ([zannkukai](https://github.com/zannkukai))
- search: fix author facet of BnF import search view [\#1572](https://github.com/rero/rero-ils/pull/1572) ([rerowep](https://github.com/rerowep))

**Closed issues:**

- Remove unnecessary description in the loan JSON schema [\#1565](https://github.com/rero/rero-ils/issues/1565)
- Field `patterns` should be optional in the holdings [\#1539](https://github.com/rero/rero-ils/issues/1539)
- A library should have as many pickup locations as wanted [\#1341](https://github.com/rero/rero-ils/issues/1341)
- No notification generation for some loans [\#1308](https://github.com/rero/rero-ils/issues/1308)
- A barcode should not be required when editing an expected issue instead of receiving it. [\#1287](https://github.com/rero/rero-ils/issues/1287)

**Merged pull requests:**

- tests: fix cypress tests [\#1643](https://github.com/rero/rero-ils/pull/1643) ([AoNoOokami](https://github.com/AoNoOokami))
- monitoring: monitor redis and add monitoring user [\#1626](https://github.com/rero/rero-ils/pull/1626) ([rerowep](https://github.com/rerowep))
- ci: fix coveralls issue [\#1602](https://github.com/rero/rero-ils/pull/1602) ([BadrAly](https://github.com/BadrAly))
- search: adapt suggestions to the locale [\#1588](https://github.com/rero/rero-ils/pull/1588) ([Garfield-fr](https://github.com/Garfield-fr))
- merge branch v1.0.0 [\#1585](https://github.com/rero/rero-ils/pull/1585) ([AoNoOokami](https://github.com/AoNoOokami))
- document: identify deleted contribution records [\#1545](https://github.com/rero/rero-ils/pull/1545) ([rerowep](https://github.com/rerowep))
- holdings: remove extra enum from the completeness field [\#1665](https://github.com/rero/rero-ils/pull/1665) ([BadrAly](https://github.com/BadrAly))
- documents: fix form options label/value [\#1657](https://github.com/rero/rero-ils/pull/1657) ([iGormilhit](https://github.com/iGormilhit))
- editor: display EnumerationAndChronology item field [\#1652](https://github.com/rero/rero-ils/pull/1652) ([BadrAly](https://github.com/BadrAly))
- holdings: fix is\_serial definition [\#1648](https://github.com/rero/rero-ils/pull/1648) ([BadrAly](https://github.com/BadrAly))
- document: document type [\#1638](https://github.com/rero/rero-ils/pull/1638) ([rerowep](https://github.com/rerowep))
- Complete the holdings record [\#1637](https://github.com/rero/rero-ils/pull/1637) ([BadrAly](https://github.com/BadrAly))
- release: 1.0.0 [\#1636](https://github.com/rero/rero-ils/pull/1636) ([iGormilhit](https://github.com/iGormilhit))
- Us1376 temporary item type [\#1633](https://github.com/rero/rero-ils/pull/1633) ([zannkukai](https://github.com/zannkukai))
- gh-actions: fix wrong label in stale workflow file [\#1613](https://github.com/rero/rero-ils/pull/1613) ([iGormilhit](https://github.com/iGormilhit))
- documents: improve holdings display performance [\#1611](https://github.com/rero/rero-ils/pull/1611) ([Garfield-fr](https://github.com/Garfield-fr))
- gh actions: fix wrong yaml format in stale worflow [\#1607](https://github.com/rero/rero-ils/pull/1607) ([iGormilhit](https://github.com/iGormilhit))
- gh actions: set the stale workflow [\#1605](https://github.com/rero/rero-ils/pull/1605) ([iGormilhit](https://github.com/iGormilhit))
- items: improve automatic barcode generation [\#1590](https://github.com/rero/rero-ils/pull/1590) ([zannkukai](https://github.com/zannkukai))
- search: improve ES template for configuration [\#1582](https://github.com/rero/rero-ils/pull/1582) ([rerowep](https://github.com/rerowep))
- dependencies: upgrade invenio to version 3.4 [\#1581](https://github.com/rero/rero-ils/pull/1581) ([rerowep](https://github.com/rerowep))
- documents: increase login button visibility [\#1556](https://github.com/rero/rero-ils/pull/1556) ([zannkukai](https://github.com/zannkukai))
- configuration: allow notifications sorting [\#1553](https://github.com/rero/rero-ils/pull/1553) ([zannkukai](https://github.com/zannkukai))
- patrons: fix document title in the fees tab [\#1548](https://github.com/rero/rero-ils/pull/1548) ([zannkukai](https://github.com/zannkukai))
- items: inherit holdings first call\_number [\#1538](https://github.com/rero/rero-ils/pull/1538) ([BadrAly](https://github.com/BadrAly))

## [v0.15.0](https://github.com/rero/rero-ils/tree/v0.15.0) (2020-12-16)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.14.1...v0.15.0)

**Implemented enhancements:**

- document: unable to edit a document \(duplicated from an ebook\) [\#1542](https://github.com/rero/rero-ils/issues/1542)
- patron: use the subscription end date as the patron expiration date, if it exists [\#1524](https://github.com/rero/rero-ils/issues/1524)
- Notes on items should be displayed in professional document detailed view [\#1501](https://github.com/rero/rero-ils/issues/1501)
- Language menu in the public interface should not be in "Menu" [\#1466](https://github.com/rero/rero-ils/issues/1466)
- The `new acquisition` toggle should be disabled by default for issue items [\#1449](https://github.com/rero/rero-ils/issues/1449)
- Prediction pattern: add ability to use ordinal numbers [\#948](https://github.com/rero/rero-ils/issues/948)
- Set the focus in the forms. [\#542](https://github.com/rero/rero-ils/issues/542)
- Fields `startDate` and `endDate` in `provisionActivity` title and description should be improved [\#1424](https://github.com/rero/rero-ils/issues/1424)
- The manual blocking of a user should block also the renewals. [\#1383](https://github.com/rero/rero-ils/issues/1383)
- The user account should be made more visible, at least on public interface. [\#1332](https://github.com/rero/rero-ils/issues/1332)
- Labels of the circulation policy editor shoud be improved. [\#1305](https://github.com/rero/rero-ils/issues/1305)
- Put better labels for checkin/checkout pages [\#1280](https://github.com/rero/rero-ils/issues/1280)

**Fixed bugs:**

- Loading the professional interface with the role editor should display a permission error [\#1508](https://github.com/rero/rero-ils/issues/1508)
- Status facet is not working in the inventory list [\#1507](https://github.com/rero/rero-ils/issues/1507)
- Error message when checking out a 'no checkout' item should be useful to the librarian [\#1470](https://github.com/rero/rero-ils/issues/1470)
- The patron loan transaction history does not always display the item and the document title. [\#1369](https://github.com/rero/rero-ils/issues/1369)
- The link to patron profil in the notification is not correct [\#1353](https://github.com/rero/rero-ils/issues/1353)
- serial pattern preview type error [\#1351](https://github.com/rero/rero-ils/issues/1351)
- Save as a template does not always create a template [\#1331](https://github.com/rero/rero-ils/issues/1331)
- When a new self registered user access to a document detailed view, an internal server error is raised [\#1255](https://github.com/rero/rero-ils/issues/1255)
- Switching library to place a request for a patron, result in a none displayed requests [\#1150](https://github.com/rero/rero-ils/issues/1150)
- Unused RERO\_ILS environment variables [\#546](https://github.com/rero/rero-ils/issues/546)
- holdings detailed view page is broken [\#1562](https://github.com/rero/rero-ils/issues/1562)
- User profile: sometimes the document field of the overdue item in the fees tab is empty. [\#1543](https://github.com/rero/rero-ils/issues/1543)
- jsonschema form is loaded two times in document editor [\#1531](https://github.com/rero/rero-ils/issues/1531)
- Counter is missing in the history tab [\#1515](https://github.com/rero/rero-ils/issues/1515)
- Changing the affiliation library of a librarian makes the editor spin for ever. [\#1510](https://github.com/rero/rero-ils/issues/1510)
- Series statement, color content, mode of issuance should be translated on professional interface [\#1488](https://github.com/rero/rero-ils/issues/1488)
- Fees history: the link of the item is wrong. [\#1487](https://github.com/rero/rero-ils/issues/1487)
- The counter of the tab 'to pickup' is not refreshed automatically [\#1482](https://github.com/rero/rero-ils/issues/1482)
- "Show more" button displayed wrongly and problematic counter [\#1400](https://github.com/rero/rero-ils/issues/1400)
- The application section of the circulation policy editor does not behave as expected. [\#1363](https://github.com/rero/rero-ils/issues/1363)
- A lot of document country codes have not been imported. [\#1328](https://github.com/rero/rero-ils/issues/1328)
- Logout from professional interface raises a 404 error [\#1322](https://github.com/rero/rero-ils/issues/1322)
- ILL request form is not translated [\#1320](https://github.com/rero/rero-ils/issues/1320)
- Toggle buttons are not translated. [\#1306](https://github.com/rero/rero-ils/issues/1306)
- Same "partOf" field generated twice [\#1242](https://github.com/rero/rero-ils/issues/1242)
- circulation: add control on circulation operation [\#1502](https://github.com/rero/rero-ils/pull/1502) ([zannkukai](https://github.com/zannkukai))

**Security fixes:**

- Static files on production delivers more file than expected ie. package-lock.json [\#713](https://github.com/rero/rero-ils/issues/713)

**Closed issues:**

- Do not expose currency codes to the translation worflow [\#1519](https://github.com/rero/rero-ils/issues/1519)
- Add a pager to the brief view of the import from BnF [\#1491](https://github.com/rero/rero-ils/issues/1491)
- Error : ExpressionChangedAfterItHasBeenCheckedError into console [\#1002](https://github.com/rero/rero-ils/issues/1002)
- Displayed page after creation/update of a ressource [\#376](https://github.com/rero/rero-ils/issues/376)
- In the patron account, the email should not depend on the communication channel. [\#1499](https://github.com/rero/rero-ils/issues/1499)
- Some circulation policy fields can have negative values or be zero. [\#1365](https://github.com/rero/rero-ils/issues/1365)
- The loans in transit to house are not displayed in the patron history. [\#1360](https://github.com/rero/rero-ils/issues/1360)

**Merged pull requests:**

- search: fix broken collection search page [\#1567](https://github.com/rero/rero-ils/pull/1567) ([jma](https://github.com/jma))
- build\(deps\): bump ini from 1.3.5 to 1.3.8 in /tests/e2e/cypress [\#1560](https://github.com/rero/rero-ils/pull/1560) ([dependabot[bot]](https://github.com/apps/dependabot))
- ci: fix github actions [\#1554](https://github.com/rero/rero-ils/pull/1554) ([rerowep](https://github.com/rerowep))
- circulation: fix transaction end\_date. [\#1532](https://github.com/rero/rero-ils/pull/1532) ([zannkukai](https://github.com/zannkukai))
- permissions: fix error message for users [\#1520](https://github.com/rero/rero-ils/pull/1520) ([Garfield-fr](https://github.com/Garfield-fr))
- document: fix call number display. [\#1568](https://github.com/rero/rero-ils/pull/1568) ([zannkukai](https://github.com/zannkukai))
- users: allows the 2nd email to be the only one [\#1561](https://github.com/rero/rero-ils/pull/1561) ([jma](https://github.com/jma))
- Implement the keep loan history patron setting \(US 1422\) [\#1552](https://github.com/rero/rero-ils/pull/1552) ([BadrAly](https://github.com/BadrAly))
- invenio-circulation: upgrade to version v1.0.0a29 [\#1551](https://github.com/rero/rero-ils/pull/1551) ([BadrAly](https://github.com/BadrAly))
- sip2: return circulation notes [\#1550](https://github.com/rero/rero-ils/pull/1550) ([lauren-d](https://github.com/lauren-d))
- serials: fix claim task [\#1546](https://github.com/rero/rero-ils/pull/1546) ([lauren-d](https://github.com/lauren-d))
- assets: move to webpack [\#1537](https://github.com/rero/rero-ils/pull/1537) ([jma](https://github.com/jma))
- vendors: do not translate currency codes [\#1536](https://github.com/rero/rero-ils/pull/1536) ([Garfield-fr](https://github.com/Garfield-fr))
- Implement SIP2 checkin/checkout actions \(US 1357\) [\#1535](https://github.com/rero/rero-ils/pull/1535) ([lauren-d](https://github.com/lauren-d))
- data: fix field partOf multiple generation [\#1523](https://github.com/rero/rero-ils/pull/1523) ([reropag](https://github.com/reropag))
- menu: update the language menu entry [\#1504](https://github.com/rero/rero-ils/pull/1504) ([zannkukai](https://github.com/zannkukai))
- dependencies: update after v0.14.1 [\#1500](https://github.com/rero/rero-ils/pull/1500) ([rerowep](https://github.com/rerowep))
- documentation: improve issues templates [\#1497](https://github.com/rero/rero-ils/pull/1497) ([iGormilhit](https://github.com/iGormilhit))
- users: allow librarian with multiple libraries [\#1496](https://github.com/rero/rero-ils/pull/1496) ([Garfield-fr](https://github.com/Garfield-fr))
- circulation: allow overriding exception [\#1494](https://github.com/rero/rero-ils/pull/1494) ([zannkukai](https://github.com/zannkukai))
- circulation: allow 'less than one day' checkout [\#1477](https://github.com/rero/rero-ils/pull/1477) ([AoNoOokami](https://github.com/AoNoOokami))
- UI: improve account menu entry visibility [\#1465](https://github.com/rero/rero-ils/pull/1465) ([zannkukai](https://github.com/zannkukai))
- tests: fix Cypress tests after v0.14.0 [\#1448](https://github.com/rero/rero-ils/pull/1448) ([AoNoOokami](https://github.com/AoNoOokami))
- circulation: update ILL request JSON schema [\#1441](https://github.com/rero/rero-ils/pull/1441) ([zannkukai](https://github.com/zannkukai))
- git: update PR template [\#1433](https://github.com/rero/rero-ils/pull/1433) ([AoNoOokami](https://github.com/AoNoOokami))
- document: improve provision activity date fields [\#1432](https://github.com/rero/rero-ils/pull/1432) ([AoNoOokami](https://github.com/AoNoOokami))
- data: implements local fields [\#1410](https://github.com/rero/rero-ils/pull/1410) ([Garfield-fr](https://github.com/Garfield-fr))

## [v0.14.1](https://github.com/rero/rero-ils/tree/v0.14.1) (2020-11-24)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.14.0...v0.14.1)

**Implemented enhancements:**

- The patron email should be required if the communication channel is email. [\#1455](https://github.com/rero/rero-ils/issues/1455)
- Holdings Editor: extra titles for the location and circulation\_category fields [\#1452](https://github.com/rero/rero-ils/issues/1452)
- MEF ID for a person \(agent\) is not on same line [\#131](https://github.com/rero/rero-ils/issues/131)

**Fixed bugs:**

- Thumbnails and document types are not displayed in the public detailed view. [\#1396](https://github.com/rero/rero-ils/issues/1396)
- Message for a request that is denied is partially untranslated. [\#1367](https://github.com/rero/rero-ils/issues/1367)
- Bulle items with item type of other organisation [\#1326](https://github.com/rero/rero-ils/issues/1326)
- Note labels for holdings are not translated in the professional interface [\#1319](https://github.com/rero/rero-ils/issues/1319)
- Internal server error when an exhibition has an empty library field   [\#1481](https://github.com/rero/rero-ils/issues/1481)
- Patron without email is not able to change his personal informations [\#1459](https://github.com/rero/rero-ils/issues/1459)
- Changing the patron the email in the RERO ID does not sync in the user resource. [\#1458](https://github.com/rero/rero-ils/issues/1458)
- Creating a user with a patron role and with an existing RERO ID email does not works. [\#1454](https://github.com/rero/rero-ils/issues/1454)
- Cancel button does not work correctly after loading templates [\#1453](https://github.com/rero/rero-ils/issues/1453)
- Holdings Editor: vendor field can not be deselected [\#1451](https://github.com/rero/rero-ils/issues/1451)
- Patterns preview does not work any more after an error 400 [\#1450](https://github.com/rero/rero-ils/issues/1450)
- In the patron account of the professional interface, the fee tab contains labels not translated. [\#1371](https://github.com/rero/rero-ils/issues/1371)
- The link to the patron profile is not translated in the public interface. [\#1283](https://github.com/rero/rero-ils/issues/1283)
- The roles are not translated in the user editor. [\#1282](https://github.com/rero/rero-ils/issues/1282)
- modeOfIssuance conversion is sometimes wrong [\#1243](https://github.com/rero/rero-ils/issues/1243)

**Closed issues:**

- \[\] should not be removed from field "responsibilityStatement" [\#1406](https://github.com/rero/rero-ils/issues/1406)

**Merged pull requests:**

- collection: fix public view [\#1484](https://github.com/rero/rero-ils/pull/1484) ([AoNoOokami](https://github.com/AoNoOokami))
- dojson: update convertion for IdRef links [\#1480](https://github.com/rero/rero-ils/pull/1480) ([rerowep](https://github.com/rerowep))
- data: set several minLength to 1 [\#1479](https://github.com/rero/rero-ils/pull/1479) ([BadrAly](https://github.com/BadrAly))
- notes: allow notes of short size [\#1476](https://github.com/rero/rero-ils/pull/1476) ([BadrAly](https://github.com/BadrAly))
- release: v0.14.1 [\#1472](https://github.com/rero/rero-ils/pull/1472) ([iGormilhit](https://github.com/iGormilhit))
- tests: fix sort title error [\#1464](https://github.com/rero/rero-ils/pull/1464) ([rerowep](https://github.com/rerowep))
- patrons: fix patron creation and modification [\#1463](https://github.com/rero/rero-ils/pull/1463) ([jma](https://github.com/jma))
- data: fix responsibilityStatement conversion [\#1461](https://github.com/rero/rero-ils/pull/1461) ([reropag](https://github.com/reropag))
- holdings: remove extra titles for some fields in editor [\#1457](https://github.com/rero/rero-ils/pull/1457) ([BadrAly](https://github.com/BadrAly))
- CI: fix github actions [\#1446](https://github.com/rero/rero-ils/pull/1446) ([rerowep](https://github.com/rerowep))
- ui: fix translation issues [\#1429](https://github.com/rero/rero-ils/pull/1429) ([AoNoOokami](https://github.com/AoNoOokami))
- frontpage: fix patron profile link translation  [\#1413](https://github.com/rero/rero-ils/pull/1413) ([AoNoOokami](https://github.com/AoNoOokami))
- metadata: adds corporate bodies to contributions [\#1274](https://github.com/rero/rero-ils/pull/1274) ([rerowep](https://github.com/rerowep))

## [v0.14.0](https://github.com/rero/rero-ils/tree/v0.14.0) (2020-11-16)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.13.1...v0.14.0)

**Implemented enhancements:**

- Sort issues by unit in the document detailed view [\#1437](https://github.com/rero/rero-ils/issues/1437)
- Add export functionality to the Late issues screen [\#1435](https://github.com/rero/rero-ils/issues/1435)
- Search by patron name and have an autocomplete in the checkin/checkout form [\#1364](https://github.com/rero/rero-ils/issues/1364)
- Identifier qualifier, status and note should be displayed in the document detailed view [\#1403](https://github.com/rero/rero-ils/issues/1403)
- On the document detailed view of the public interface, the due date should display the time [\#1398](https://github.com/rero/rero-ils/issues/1398)
- Don't display birth date on top of public patron account [\#1386](https://github.com/rero/rero-ils/issues/1386)
- Replace patron barcode by patron number in the public patron account [\#1385](https://github.com/rero/rero-ils/issues/1385)
- In the check-in form, the patron information can be more useful \(link + age\). [\#1378](https://github.com/rero/rero-ils/issues/1378)
- Display disabled "renew" button in patron account of the public interface [\#1357](https://github.com/rero/rero-ils/issues/1357)
- Display the authors in the requests \(pending and at desk\) of the pro patron account [\#1355](https://github.com/rero/rero-ils/issues/1355)
- The checkouts should be sorted by due date in patron account. [\#1296](https://github.com/rero/rero-ils/issues/1296)
- The patron account tab should contain the count of the items. [\#1278](https://github.com/rero/rero-ils/issues/1278)

**Fixed bugs:**

- In the pro patron account, some paid fees still appear. [\#1373](https://github.com/rero/rero-ils/issues/1373)
- Item CHECKIN\_1\_1\_2 does not work [\#1334](https://github.com/rero/rero-ils/issues/1334)
- A system librarian without role librarian doesn't have all rights and has bugs [\#1340](https://github.com/rero/rero-ils/issues/1340)
- issue with the patron subscription renewal task [\#1317](https://github.com/rero/rero-ils/issues/1317)
- Requests in the queue are not correctly ordered. [\#1314](https://github.com/rero/rero-ils/issues/1314)
- Cannot delete a request of an item with multiple requests. [\#1303](https://github.com/rero/rero-ils/issues/1303)
- Display the pickup location name in the circulation interface [\#1300](https://github.com/rero/rero-ils/issues/1300)
- circulation: a staff cannot delete a request of an item with the status 'at desk' [\#1293](https://github.com/rero/rero-ils/issues/1293)
- "Fees" is not translated in the patron account of the professional interface [\#1281](https://github.com/rero/rero-ils/issues/1281)
- The help link on home page is deprecated. [\#1277](https://github.com/rero/rero-ils/issues/1277)
- After a renewal, the new due date is not displayed in the professional view [\#1256](https://github.com/rero/rero-ils/issues/1256)
- circulation: check in an item with no loans [\#1408](https://github.com/rero/rero-ils/pull/1408) ([BadrAly](https://github.com/BadrAly))
- transactions: fix paid fees still opened [\#1404](https://github.com/rero/rero-ils/pull/1404) ([zannkukai](https://github.com/zannkukai))

**Closed issues:**

- Cypress: use access token for operations that are not part of a test \(before & after\) [\#1221](https://github.com/rero/rero-ils/issues/1221)
- A user without the editor role should not be able to delete file. [\#1289](https://github.com/rero/rero-ils/issues/1289)
- Identifier type not translated in document detailed view [\#918](https://github.com/rero/rero-ils/issues/918)

**Merged pull requests:**

- V0.14 [\#1402](https://github.com/rero/rero-ils/pull/1402) ([zannkukai](https://github.com/zannkukai))
- holdings: make vendor field optional [\#1442](https://github.com/rero/rero-ils/pull/1442) ([BadrAly](https://github.com/BadrAly))
- acquisition: implements serial claims [\#1439](https://github.com/rero/rero-ils/pull/1439) ([BadrAly](https://github.com/BadrAly))
- deployment: fix poetry version to \< 1.1.0 [\#1430](https://github.com/rero/rero-ils/pull/1430) ([rerowep](https://github.com/rerowep))
- release: v0.14.0 [\#1427](https://github.com/rero/rero-ils/pull/1427) ([iGormilhit](https://github.com/iGormilhit))
- patrons: manage patrons without e-mail [\#1418](https://github.com/rero/rero-ils/pull/1418) ([jma](https://github.com/jma))
- document: fix identifier display in detail view [\#1416](https://github.com/rero/rero-ils/pull/1416) ([AoNoOokami](https://github.com/AoNoOokami))
- document: fix due date in detailed view [\#1414](https://github.com/rero/rero-ils/pull/1414) ([AoNoOokami](https://github.com/AoNoOokami))
- public ui: improve displayed information [\#1411](https://github.com/rero/rero-ils/pull/1411) ([zannkukai](https://github.com/zannkukai))
- cypress: improve tests [\#1409](https://github.com/rero/rero-ils/pull/1409) ([AoNoOokami](https://github.com/AoNoOokami))
- app: update help link on the frontpage [\#1304](https://github.com/rero/rero-ils/pull/1304) ([AoNoOokami](https://github.com/AoNoOokami))

## [v0.13.1](https://github.com/rero/rero-ils/tree/v0.13.1) (2020-11-05)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.13.0...v0.13.1)

**Implemented enhancements:**

- An e-mail without complete domain name can be saved in the patron editor [\#1381](https://github.com/rero/rero-ils/issues/1381)
- Rename the request status "ready" into "to pick up" in the patron account of the public interface [\#1356](https://github.com/rero/rero-ils/issues/1356)
- A value for the field "title" with type "bf:Title" should be required. [\#1286](https://github.com/rero/rero-ils/issues/1286)
- The non required fields of the document editor should support default values. [\#1119](https://github.com/rero/rero-ils/issues/1119)

**Fixed bugs:**

- ILSPILOT: Add a subscription for patron [\#1349](https://github.com/rero/rero-ils/issues/1349)
- The "Home" link in the help is not translated. [\#1333](https://github.com/rero/rero-ils/issues/1333)
- Patron lastname/firstname are reversed for the requests [\#1297](https://github.com/rero/rero-ils/issues/1297)
- Fees are not updated instantly. [\#1294](https://github.com/rero/rero-ils/issues/1294)
- Selector with possible multiple value are not alphabetically sorted [\#1231](https://github.com/rero/rero-ils/issues/1231)
- Default values for prediction patterns are translated [\#1022](https://github.com/rero/rero-ils/issues/1022)

**Closed issues:**

- The description of the user/patron `street` field should not ask for a coma. [\#1382](https://github.com/rero/rero-ils/issues/1382)

**Merged pull requests:**

- tests: force npm version for github actions [\#1388](https://github.com/rero/rero-ils/pull/1388) ([jma](https://github.com/jma))
- patrons: fix patron editor [\#1368](https://github.com/rero/rero-ils/pull/1368) ([jma](https://github.com/jma))
- editor: restore default value for hidden field [\#1338](https://github.com/rero/rero-ils/pull/1338) ([jma](https://github.com/jma))
- release: v0.13.1 [\#1323](https://github.com/rero/rero-ils/pull/1323) ([iGormilhit](https://github.com/iGormilhit))
- facets: fix contribution filter [\#1316](https://github.com/rero/rero-ils/pull/1316) ([lauren-d](https://github.com/lauren-d))
- ill\_request: fix form validation problem [\#1315](https://github.com/rero/rero-ils/pull/1315) ([zannkukai](https://github.com/zannkukai))

## [v0.13.0](https://github.com/rero/rero-ils/tree/v0.13.0) (2020-10-19)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.12.0...v0.13.0)

**Implemented enhancements:**

- The canton dropdown should appear only if the country Switzerland is selected. [\#1285](https://github.com/rero/rero-ils/issues/1285)
- Holding : expected date should be today's date by default [\#1249](https://github.com/rero/rero-ils/issues/1249)
- circulation: need a better response time for the patron account \(public/pro interface\) [\#1246](https://github.com/rero/rero-ils/issues/1246)
- The date in the data should be better checked. [\#1187](https://github.com/rero/rero-ils/issues/1187)
- Every document should have a `provisionActivity` field [\#1132](https://github.com/rero/rero-ils/issues/1132)
- maximum number of results  [\#112](https://github.com/rero/rero-ils/issues/112)
- The help menu should point to the public help page if clicked from public interface [\#1127](https://github.com/rero/rero-ils/issues/1127)
- monitoring: fix es duplicate monitoring [\#1206](https://github.com/rero/rero-ils/pull/1206) ([rerowep](https://github.com/rerowep))

**Fixed bugs:**

- New due date is not displayed after a renewal in pro interface. [\#1279](https://github.com/rero/rero-ils/issues/1279)
- circulation: unable to display a patron account in public view when he has a dispute. [\#1272](https://github.com/rero/rero-ils/issues/1272)
- Write a full sentence: The edit button should not be activated for not logged in users. [\#1265](https://github.com/rero/rero-ils/issues/1265)
- circulation: change text in courtesy notification [\#1264](https://github.com/rero/rero-ils/issues/1264)
- Holdings for journals have various problems [\#1252](https://github.com/rero/rero-ils/issues/1252)
- A due\_soon notification should not have "Not renewable" [\#1342](https://github.com/rero/rero-ils/issues/1342)
- The circulation interface mixes item barcodes between organisations. [\#1085](https://github.com/rero/rero-ils/issues/1085)

**Closed issues:**

- A call number \(1st and 2nd\) should not have a minimum caracter constraint. [\#1284](https://github.com/rero/rero-ils/issues/1284)
- The patron first and last names are inverted in circulation UI. [\#1230](https://github.com/rero/rero-ils/issues/1230)
- Cypress: find a way to preserve auth info and server in 'after' part of tests [\#1220](https://github.com/rero/rero-ils/issues/1220)
- Make isort consistent for Travis and local development [\#816](https://github.com/rero/rero-ils/issues/816)
- elasticsearch document\_type deprecated [\#83](https://github.com/rero/rero-ils/issues/83)
- new cookiecutter [\#80](https://github.com/rero/rero-ils/issues/80)
- Results page: Unable to extend a search to all organisations in professional view. [\#975](https://github.com/rero/rero-ils/issues/975)
- Impossible to request a document of another library [\#927](https://github.com/rero/rero-ils/issues/927)

**Merged pull requests:**

- release: 0.13.0 [\#1313](https://github.com/rero/rero-ils/pull/1313) ([jma](https://github.com/jma))
- refactors user resource [\#1302](https://github.com/rero/rero-ils/pull/1302) ([jma](https://github.com/jma))
- patron: Fix user import problem. [\#1292](https://github.com/rero/rero-ils/pull/1292) ([zannkukai](https://github.com/zannkukai))
- implements template resource for document, holdings, item and patron records [\#1275](https://github.com/rero/rero-ils/pull/1275) ([zannkukai](https://github.com/zannkukai))
- monitoring: display db connection counts [\#1271](https://github.com/rero/rero-ils/pull/1271) ([rerowep](https://github.com/rerowep))
- circulation: change text in courtesy notification [\#1266](https://github.com/rero/rero-ils/pull/1266) ([benerken](https://github.com/benerken))
- document: fix internal server error when display view [\#1263](https://github.com/rero/rero-ils/pull/1263) ([lauren-d](https://github.com/lauren-d))
- circulation: increase loan API performance [\#1262](https://github.com/rero/rero-ils/pull/1262) ([zannkukai](https://github.com/zannkukai))
- tests: Use github actions [\#1258](https://github.com/rero/rero-ils/pull/1258) ([rerowep](https://github.com/rerowep))
- ill\_request: merge US to dev [\#1251](https://github.com/rero/rero-ils/pull/1251) ([zannkukai](https://github.com/zannkukai))
- deploy: fix lxml error [\#1248](https://github.com/rero/rero-ils/pull/1248) ([jma](https://github.com/jma))
- celery: use celery 5.0.0 [\#1247](https://github.com/rero/rero-ils/pull/1247) ([zannkukai](https://github.com/zannkukai))
- celery: fix 'celery-config' fixture [\#1245](https://github.com/rero/rero-ils/pull/1245) ([zannkukai](https://github.com/zannkukai))
- general: use better regular expression for date [\#1239](https://github.com/rero/rero-ils/pull/1239) ([zannkukai](https://github.com/zannkukai))
- patrons: fix patrons search api [\#1307](https://github.com/rero/rero-ils/pull/1307) ([jma](https://github.com/jma))
- patron: fix patron profile for dispute event [\#1299](https://github.com/rero/rero-ils/pull/1299) ([zannkukai](https://github.com/zannkukai))
- implements collection resource [\#1267](https://github.com/rero/rero-ils/pull/1267) ([AoNoOokami](https://github.com/AoNoOokami))
- holdings: add optional fields for holdings display [\#1244](https://github.com/rero/rero-ils/pull/1244) ([BadrAly](https://github.com/BadrAly))
- translation: standardization of enumerations with form options [\#1238](https://github.com/rero/rero-ils/pull/1238) ([Garfield-fr](https://github.com/Garfield-fr))
- loan: fix patron name [\#1232](https://github.com/rero/rero-ils/pull/1232) ([AoNoOokami](https://github.com/AoNoOokami))
- merge US1489 circulation cypress tests [\#1215](https://github.com/rero/rero-ils/pull/1215) ([AoNoOokami](https://github.com/AoNoOokami))
- indexer: fix bulk indexing [\#1202](https://github.com/rero/rero-ils/pull/1202) ([rerowep](https://github.com/rerowep))
- acquisition: add document selector for order lines [\#1185](https://github.com/rero/rero-ils/pull/1185) ([lauren-d](https://github.com/lauren-d))
- dependencies: update to ES7 and invenio 3.3 [\#1175](https://github.com/rero/rero-ils/pull/1175) ([rerowep](https://github.com/rerowep))
- help: update the public help menu entry url [\#1172](https://github.com/rero/rero-ils/pull/1172) ([zannkukai](https://github.com/zannkukai))
- wiki: update the public help menu entry url [\#1162](https://github.com/rero/rero-ils/pull/1162) ([zannkukai](https://github.com/zannkukai))

## [v0.12.0](https://github.com/rero/rero-ils/tree/v0.12.0) (2020-09-21)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.12.0rc...v0.12.0)

**Implemented enhancements:**

- Switch to professional interface at login [\#933](https://github.com/rero/rero-ils/issues/933)

**Fixed bugs:**

- The BnF import is wrong for provision activity. [\#1219](https://github.com/rero/rero-ils/issues/1219)
- State of button on/off in circulation policy editor [\#891](https://github.com/rero/rero-ils/issues/891)
- A wrong message appears on the document detailed view of the professional interface [\#1223](https://github.com/rero/rero-ils/issues/1223)
- message 'prêt impossible' : l'exemplaire est demandé par un autre lecteur [\#1160](https://github.com/rero/rero-ils/issues/1160)
- celery scheduler can not locate the method task\_clear\_and\_renew\_subscriptions [\#1158](https://github.com/rero/rero-ils/issues/1158)
- Public patron profile view raises an error 500 [\#1145](https://github.com/rero/rero-ils/issues/1145)
- Contributors without MEF links not displayed in pro detailed view [\#1030](https://github.com/rero/rero-ils/issues/1030)

**Closed issues:**

- Network protection and "any later version" removed from license [\#1186](https://github.com/rero/rero-ils/issues/1186)
- Removing existing restriction on available pickup location prevents to save the record [\#988](https://github.com/rero/rero-ils/issues/988)
- Check that all buttons \(from UI\) follow the circulation policy [\#936](https://github.com/rero/rero-ils/issues/936)
- Translations of roles in patron editor [\#881](https://github.com/rero/rero-ils/issues/881)
- No action is performed in checkin form [\#831](https://github.com/rero/rero-ils/issues/831)
- Checked in item from other library doesn't go in transit [\#813](https://github.com/rero/rero-ils/issues/813)
- Checkin of item on shelf, with request to validate [\#801](https://github.com/rero/rero-ils/issues/801)
- Checkin on item on shelf from other library [\#800](https://github.com/rero/rero-ils/issues/800)
- Version v0.12.0rc is missing existing translations [\#1222](https://github.com/rero/rero-ils/issues/1222)

**Merged pull requests:**

- release: v0.12.0 [\#1235](https://github.com/rero/rero-ils/pull/1235) ([jma](https://github.com/jma))
- translations: translate for release v0.12.0 [\#1234](https://github.com/rero/rero-ils/pull/1234) ([jma](https://github.com/jma))
- patron: fix profile translations [\#1229](https://github.com/rero/rero-ils/pull/1229) ([Garfield-fr](https://github.com/Garfield-fr))
- dojson: fix unimarc publishers provision activity [\#1224](https://github.com/rero/rero-ils/pull/1224) ([rerowep](https://github.com/rerowep))
- release: v0.12.0rc [\#1210](https://github.com/rero/rero-ils/pull/1210) ([iGormilhit](https://github.com/iGormilhit))
- persons: fix public search count [\#1205](https://github.com/rero/rero-ils/pull/1205) ([rerowep](https://github.com/rerowep))
- holdings: allow creating std holdings on journal [\#1197](https://github.com/rero/rero-ils/pull/1197) ([BadrAly](https://github.com/BadrAly))
- search: remove useless translated facets [\#1195](https://github.com/rero/rero-ils/pull/1195) ([lauren-d](https://github.com/lauren-d))
- document: replace role label content with values [\#1194](https://github.com/rero/rero-ils/pull/1194) ([iGormilhit](https://github.com/iGormilhit))
- editor: fix error 400 when saving a simple document [\#1192](https://github.com/rero/rero-ils/pull/1192) ([AoNoOokami](https://github.com/AoNoOokami))
- package: update dependencies [\#1191](https://github.com/rero/rero-ils/pull/1191) ([BadrAly](https://github.com/BadrAly))
- US1546 marcxml support [\#1189](https://github.com/rero/rero-ils/pull/1189) ([BadrAly](https://github.com/BadrAly))
- circulation: fix validate request return type [\#1177](https://github.com/rero/rero-ils/pull/1177) ([zannkukai](https://github.com/zannkukai))
- circulation: fix change pickup location on loans [\#1174](https://github.com/rero/rero-ils/pull/1174) ([BadrAly](https://github.com/BadrAly))
- permission: refactoring the loan permission factory [\#1170](https://github.com/rero/rero-ils/pull/1170) ([zannkukai](https://github.com/zannkukai))
- circulation: allow requests on ITEM\_IN\_TRANSIT\_TO\_HOUSE loans. [\#1169](https://github.com/rero/rero-ils/pull/1169) ([BadrAly](https://github.com/BadrAly))
- inventory: export document creator field [\#1163](https://github.com/rero/rero-ils/pull/1163) ([lauren-d](https://github.com/lauren-d))
- data: reorganisation of json schema. [\#1156](https://github.com/rero/rero-ils/pull/1156) ([rerowep](https://github.com/rerowep))
- marc21tojson: fix transformation errors [\#1134](https://github.com/rero/rero-ils/pull/1134) ([rerowep](https://github.com/rerowep))
- item: update item/doc for new acquisition [\#1130](https://github.com/rero/rero-ils/pull/1130) ([zannkukai](https://github.com/zannkukai))
- data model: implement contribution [\#1129](https://github.com/rero/rero-ils/pull/1129) ([rerowep](https://github.com/rerowep))
- SIP2: implement patron information [\#1096](https://github.com/rero/rero-ils/pull/1096) ([lauren-d](https://github.com/lauren-d))

## [v0.12.0rc](https://github.com/rero/rero-ils/tree/v0.12.0rc) (2020-09-14)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.11.0...v0.12.0rc)

**Implemented enhancements:**

- scripts: install ng-core and ui in main project [\#1142](https://github.com/rero/rero-ils/pull/1142) ([blankoworld](https://github.com/blankoworld))
- cypress: enhance Cypress commands precision [\#1136](https://github.com/rero/rero-ils/pull/1136) ([blankoworld](https://github.com/blankoworld))
- tests: enhance Cypress with fixtures [\#1125](https://github.com/rero/rero-ils/pull/1125) ([blankoworld](https://github.com/blankoworld))

**Fixed bugs:**

- Selects aren't alphabetically sorted when the form options have the code as value of the `label` and `value` keys [\#1149](https://github.com/rero/rero-ils/issues/1149)
- Patron profile view raises an error 410 \(error 500 displayed\) when an item of the history is deleted [\#1137](https://github.com/rero/rero-ils/issues/1137)
- documents: import EAN - some abstracts are HTML encoded [\#743](https://github.com/rero/rero-ils/issues/743)
- test: fix autoflake errors [\#1176](https://github.com/rero/rero-ils/pull/1176) ([rerowep](https://github.com/rerowep))

**Closed issues:**

- The property numbering\_script is either in the wrong file, or to be deleted [\#1147](https://github.com/rero/rero-ils/issues/1147)
- Renewal badge irrelevant for checked in items [\#797](https://github.com/rero/rero-ils/issues/797)
- UI : Replace RXJS "combineLatest"  [\#549](https://github.com/rero/rero-ils/issues/549)

**Merged pull requests:**

- utils: new method to return record class [\#1183](https://github.com/rero/rero-ils/pull/1183) ([BadrAly](https://github.com/BadrAly))
- Translations update from Weblate [\#1171](https://github.com/rero/rero-ils/pull/1171) ([weblate](https://github.com/weblate))
- US1394 invenio circulation [\#1166](https://github.com/rero/rero-ils/pull/1166) ([BadrAly](https://github.com/BadrAly))
- patron: fix missing configuration for patron subscriptions [\#1159](https://github.com/rero/rero-ils/pull/1159) ([BadrAly](https://github.com/BadrAly))
- Translations update from Weblate [\#1154](https://github.com/rero/rero-ils/pull/1154) ([weblate](https://github.com/weblate))
- Translations update from Weblate [\#1153](https://github.com/rero/rero-ils/pull/1153) ([weblate](https://github.com/weblate))
- patron profile: fix for plural translation [\#1148](https://github.com/rero/rero-ils/pull/1148) ([Garfield-fr](https://github.com/Garfield-fr))
- Translations update from Weblate [\#1141](https://github.com/rero/rero-ils/pull/1141) ([weblate](https://github.com/weblate))
- patron: no history returned for deleted items [\#1139](https://github.com/rero/rero-ils/pull/1139) ([BadrAly](https://github.com/BadrAly))
- Translations update from Weblate [\#1138](https://github.com/rero/rero-ils/pull/1138) ([weblate](https://github.com/weblate))
- Translations update from Weblate [\#1131](https://github.com/rero/rero-ils/pull/1131) ([weblate](https://github.com/weblate))
- patron account: add fees tab [\#1124](https://github.com/rero/rero-ils/pull/1124) ([Garfield-fr](https://github.com/Garfield-fr))
- cli: marc21json cli function to use splitted json schemas [\#1120](https://github.com/rero/rero-ils/pull/1120) ([rerowep](https://github.com/rerowep))
- cypress: test the creation of a simple document [\#1116](https://github.com/rero/rero-ils/pull/1116) ([AoNoOokami](https://github.com/AoNoOokami))

## [v0.11.0](https://github.com/rero/rero-ils/tree/v0.11.0) (2020-08-04)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.10.1...v0.11.0)

**Implemented enhancements:**

- Reduce size of title in document detailed view [\#880](https://github.com/rero/rero-ils/issues/880)
- server: enable options to server script [\#1115](https://github.com/rero/rero-ils/pull/1115) ([blankoworld](https://github.com/blankoworld))

**Fixed bugs:**

- Authors and issuance fields: organisation as author and subtype are not loaded correctly when editing a record with those fields [\#1102](https://github.com/rero/rero-ils/issues/1102)
- Editor: "jump to" not always working [\#1035](https://github.com/rero/rero-ils/issues/1035)
- Autocomplete stays even after the results list is displayed [\#898](https://github.com/rero/rero-ils/issues/898)

**Closed issues:**

- The tab order of the document detailed view \(pro interface\) should be: get / description [\#1078](https://github.com/rero/rero-ils/issues/1078)
- Document type "Other" not translated in document detailed view \(public interface\) [\#917](https://github.com/rero/rero-ils/issues/917)
- Translate content field "Language" in document detailed view of public interface [\#916](https://github.com/rero/rero-ils/issues/916)
- Clear the patron info on top of checkin form when quiting it [\#886](https://github.com/rero/rero-ils/issues/886)
- Translations of actions realised in circulation UI [\#882](https://github.com/rero/rero-ils/issues/882)
- Impossible to save the document editor with field "notes" [\#1036](https://github.com/rero/rero-ils/issues/1036)
- editor : multiple provision activity lost when editing a document [\#1003](https://github.com/rero/rero-ils/issues/1003)
- Saving a document with edition responsibility impossible [\#906](https://github.com/rero/rero-ils/issues/906)
- Improvement needed on the request information when doing a checkin [\#883](https://github.com/rero/rero-ils/issues/883)

**Merged pull requests:**

- permission: refactoring patron linked resources permission factory [\#1123](https://github.com/rero/rero-ils/pull/1123) ([zannkukai](https://github.com/zannkukai))
- release: v0.11.0 [\#1122](https://github.com/rero/rero-ils/pull/1122) ([jma](https://github.com/jma))
- pytest: fix deprecation warnings on version 6.0.0 [\#1121](https://github.com/rero/rero-ils/pull/1121) ([blankoworld](https://github.com/blankoworld))
- documents: improve editor layout [\#1118](https://github.com/rero/rero-ils/pull/1118) ([jma](https://github.com/jma))
- permission: refactoring structure resources permission factory [\#1117](https://github.com/rero/rero-ils/pull/1117) ([zannkukai](https://github.com/zannkukai))
- Us1491 item inventory list [\#1114](https://github.com/rero/rero-ils/pull/1114) ([jma](https://github.com/jma))
- permission: refactoring acquisition resources permission factory [\#1113](https://github.com/rero/rero-ils/pull/1113) ([zannkukai](https://github.com/zannkukai))
- permission: refactoring resources permission factory [\#1110](https://github.com/rero/rero-ils/pull/1110) ([zannkukai](https://github.com/zannkukai))
- documentation: fix README weblate badge [\#1109](https://github.com/rero/rero-ils/pull/1109) ([iGormilhit](https://github.com/iGormilhit))
- deployment: node 12 [\#1108](https://github.com/rero/rero-ils/pull/1108) ([rerowep](https://github.com/rerowep))
- cypress: enhance commands to improve tests [\#1104](https://github.com/rero/rero-ils/pull/1104) ([blankoworld](https://github.com/blankoworld))
- ui: select menu items by Cypress through ids [\#1101](https://github.com/rero/rero-ils/pull/1101) ([blankoworld](https://github.com/blankoworld))
- check\_license: accept Triple Slash Directive [\#1098](https://github.com/rero/rero-ils/pull/1098) ([blankoworld](https://github.com/blankoworld))
- bootstrap scripts: fix npm utils installation [\#1088](https://github.com/rero/rero-ils/pull/1088) ([blankoworld](https://github.com/blankoworld))
- poetry: update packages to their last version [\#1087](https://github.com/rero/rero-ils/pull/1087) ([blankoworld](https://github.com/blankoworld))
- circulation: ensure the item extend loan action for frontend calls [\#1084](https://github.com/rero/rero-ils/pull/1084) ([blankoworld](https://github.com/blankoworld))
- permissions: refactoring organisation permissions [\#1051](https://github.com/rero/rero-ils/pull/1051) ([zannkukai](https://github.com/zannkukai))
- documentation: add a weblate badge to the README [\#1106](https://github.com/rero/rero-ils/pull/1106) ([iGormilhit](https://github.com/iGormilhit))
- document: index host document title in child document record [\#1095](https://github.com/rero/rero-ils/pull/1095) ([AoNoOokami](https://github.com/AoNoOokami))
- translations: prepare project for weblate [\#1092](https://github.com/rero/rero-ils/pull/1092) ([iGormilhit](https://github.com/iGormilhit))
- request: sort alphabetically pickup location [\#1090](https://github.com/rero/rero-ils/pull/1090) ([Garfield-fr](https://github.com/Garfield-fr))
- json schema: use the select menu with order [\#1086](https://github.com/rero/rero-ils/pull/1086) ([Garfield-fr](https://github.com/Garfield-fr))
- document: translate document type in detail view [\#1083](https://github.com/rero/rero-ils/pull/1083) ([zannkukai](https://github.com/zannkukai))
- editor: fix edition statement saving problem. [\#1071](https://github.com/rero/rero-ils/pull/1071) ([zannkukai](https://github.com/zannkukai))
- branch for the data model series user story [\#1069](https://github.com/rero/rero-ils/pull/1069) ([AoNoOokami](https://github.com/AoNoOokami))
- schema: split JSON schemas [\#1056](https://github.com/rero/rero-ils/pull/1056) ([rerowep](https://github.com/rerowep))

## [v0.10.1](https://github.com/rero/rero-ils/tree/v0.10.1) (2020-07-02)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.10.0...v0.10.1)

**Merged pull requests:**

- release: v0.10.1 [\#1077](https://github.com/rero/rero-ils/pull/1077) ([iGormilhit](https://github.com/iGormilhit))
- US1274: Import from BnF [\#1076](https://github.com/rero/rero-ils/pull/1076) ([iGormilhit](https://github.com/iGormilhit))

## [v0.10.0](https://github.com/rero/rero-ils/tree/v0.10.0) (2020-07-02)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.9.1...v0.10.0)

**Implemented enhancements:**

- Improvement needed on the switch library menu [\#821](https://github.com/rero/rero-ils/issues/821)

**Fixed bugs:**

- The switch library menu is not dynamically populated [\#822](https://github.com/rero/rero-ils/issues/822)

**Closed issues:**

- Restarting scheduler is disabling entries [\#1033](https://github.com/rero/rero-ils/issues/1033)
- Redirection after item deletion from the item detailed view [\#1024](https://github.com/rero/rero-ils/issues/1024)
- Language switch does not work properly on the professional interface [\#925](https://github.com/rero/rero-ils/issues/925)
- Bigger thumbnails in public view [\#903](https://github.com/rero/rero-ils/issues/903)
- Barcode and callnumber \(at item level\) shoudn't be mandatory [\#648](https://github.com/rero/rero-ils/issues/648)
- Author search in document creation display wrong date. [\#1038](https://github.com/rero/rero-ils/issues/1038)
- Librarian permissions are too large on other librarian records [\#930](https://github.com/rero/rero-ils/issues/930)
- Link to the patron profile not adapted to the concerned instance in the notification message. [\#802](https://github.com/rero/rero-ils/issues/802)
- A librarian can change his/her affiliation library in the editor [\#1039](https://github.com/rero/rero-ils/issues/1039)

**Merged pull requests:**

- Merge US1275 on dev [\#1060](https://github.com/rero/rero-ils/pull/1060) ([zannkukai](https://github.com/zannkukai))
- Zan us1351 items notes [\#1057](https://github.com/rero/rero-ils/pull/1057) ([zannkukai](https://github.com/zannkukai))
- translation: fix string extraction from JSON file [\#1054](https://github.com/rero/rero-ils/pull/1054) ([zannkukai](https://github.com/zannkukai))
- cli: correct wrong process bulk queue [\#1037](https://github.com/rero/rero-ils/pull/1037) ([lauren-d](https://github.com/lauren-d))
- scheduler: use saved enabled state of tasks [\#1034](https://github.com/rero/rero-ils/pull/1034) ([rerowep](https://github.com/rerowep))
- license: update missing info in the license [\#1031](https://github.com/rero/rero-ils/pull/1031) ([iGormilhit](https://github.com/iGormilhit))
- notifications: patron url [\#1029](https://github.com/rero/rero-ils/pull/1029) ([rerowep](https://github.com/rerowep))
- ui: keep selected tab active on reload [\#1025](https://github.com/rero/rero-ils/pull/1025) ([Garfield-fr](https://github.com/Garfield-fr))
- docs: add the missing references to the add\_request circulation action. [\#1023](https://github.com/rero/rero-ils/pull/1023) ([BadrAly](https://github.com/BadrAly))
- translations: adds editor translations support [\#1021](https://github.com/rero/rero-ils/pull/1021) ([jma](https://github.com/jma))
- scripts: correct server script [\#1015](https://github.com/rero/rero-ils/pull/1015) ([rerowep](https://github.com/rerowep))
- release: v0.10.0 [\#1074](https://github.com/rero/rero-ils/pull/1074) ([iGormilhit](https://github.com/iGormilhit))
- translations: fetch new translations [\#1072](https://github.com/rero/rero-ils/pull/1072) ([iGormilhit](https://github.com/iGormilhit))
- documentation: add an issue template for dev [\#1064](https://github.com/rero/rero-ils/pull/1064) ([iGormilhit](https://github.com/iGormilhit))
- document: fix edition with notes [\#1062](https://github.com/rero/rero-ils/pull/1062) ([AoNoOokami](https://github.com/AoNoOokami))
- documentation: configure github issue templates [\#1050](https://github.com/rero/rero-ils/pull/1050) ([iGormilhit](https://github.com/iGormilhit))
- authorization: create role management API [\#1043](https://github.com/rero/rero-ils/pull/1043) ([zannkukai](https://github.com/zannkukai))
- merge US1296 to dev \(UX of editor\) [\#1012](https://github.com/rero/rero-ils/pull/1012) ([AoNoOokami](https://github.com/AoNoOokami))
- install: integration of invenio-sip2 module [\#1005](https://github.com/rero/rero-ils/pull/1005) ([lauren-d](https://github.com/lauren-d))

## [v0.9.1](https://github.com/rero/rero-ils/tree/v0.9.1) (2020-06-03)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.9.0...v0.9.1)

**Closed issues:**

- Action realised in circulation must be in the past participle [\#890](https://github.com/rero/rero-ils/issues/890)

**Merged pull requests:**

- release: v0.9.1 [\#1019](https://github.com/rero/rero-ils/pull/1019) ([iGormilhit](https://github.com/iGormilhit))
- Documentation resources: circulation actions, reroils\_resources and loan state chart [\#1017](https://github.com/rero/rero-ils/pull/1017) ([blankoworld](https://github.com/blankoworld))
- translation: fix translations API [\#1013](https://github.com/rero/rero-ils/pull/1013) ([zannkukai](https://github.com/zannkukai))
- nginx logging [\#1007](https://github.com/rero/rero-ils/pull/1007) ([rerowep](https://github.com/rerowep))

## [v0.9.0](https://github.com/rero/rero-ils/tree/v0.9.0) (2020-06-02)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.8.0...v0.9.0)

**Implemented enhancements:**

- Workflow when seizing opening hours [\#675](https://github.com/rero/rero-ils/issues/675)
- Language facet behaviour \(number of results\) [\#91](https://github.com/rero/rero-ils/issues/91)
- An informative README is missing! [\#627](https://github.com/rero/rero-ils/issues/627)

**Closed issues:**

- Ranking of patrons [\#934](https://github.com/rero/rero-ils/issues/934)
- Permissions for item/patron types and circ policies [\#932](https://github.com/rero/rero-ils/issues/932)
- Cancel button in patron profile [\#929](https://github.com/rero/rero-ils/issues/929)
- Focus not set in many views [\#928](https://github.com/rero/rero-ils/issues/928)
- Suppress the item detailed view of the public interface [\#884](https://github.com/rero/rero-ils/issues/884)
- Persons can be indexed twice resulting in duplicate records [\#834](https://github.com/rero/rero-ils/issues/834)
- Delay for display selector content for item types at item creation [\#819](https://github.com/rero/rero-ils/issues/819)
- search: problem with brackets \[ \] in the query [\#755](https://github.com/rero/rero-ils/issues/755)
- Errors when running run\_tests.sh [\#1000](https://github.com/rero/rero-ils/issues/1000)

**Merged pull requests:**

- project: fix keyboard interruption for scripts [\#994](https://github.com/rero/rero-ils/pull/994) ([blankoworld](https://github.com/blankoworld))
- serials: introduce items of type issue [\#993](https://github.com/rero/rero-ils/pull/993) ([BadrAly](https://github.com/BadrAly))
- setup: fix old pipenv environment variables [\#992](https://github.com/rero/rero-ils/pull/992) ([blankoworld](https://github.com/blankoworld))
- patrons: check if a patron email is unique [\#990](https://github.com/rero/rero-ils/pull/990) ([jma](https://github.com/jma))
- schemas: fix patron transaction events schema [\#987](https://github.com/rero/rero-ils/pull/987) ([zannkukai](https://github.com/zannkukai))
- dependencies: use poetry [\#986](https://github.com/rero/rero-ils/pull/986) ([jma](https://github.com/jma))
- tests: fix travis trouble with pytest-invenio [\#981](https://github.com/rero/rero-ils/pull/981) ([blankoworld](https://github.com/blankoworld))
- tests: fix units testing for generated item barcodes [\#979](https://github.com/rero/rero-ils/pull/979) ([BadrAly](https://github.com/BadrAly))
- tests: fix travis [\#977](https://github.com/rero/rero-ils/pull/977) ([rerowep](https://github.com/rerowep))
- location: unique pickup location for a library [\#976](https://github.com/rero/rero-ils/pull/976) ([zannkukai](https://github.com/zannkukai))
- rest api: add simple query support [\#973](https://github.com/rero/rero-ils/pull/973) ([jma](https://github.com/jma))
- item: field call number is now optional [\#971](https://github.com/rero/rero-ils/pull/971) ([BadrAly](https://github.com/BadrAly))
- document: suppress item detail view [\#970](https://github.com/rero/rero-ils/pull/970) ([zannkukai](https://github.com/zannkukai))
- item: multiple inheritance for the item class [\#968](https://github.com/rero/rero-ils/pull/968) ([BadrAly](https://github.com/BadrAly))
- db: separate tables [\#959](https://github.com/rero/rero-ils/pull/959) ([rerowep](https://github.com/rerowep))
- enqueues notifications [\#951](https://github.com/rero/rero-ils/pull/951) ([rerowep](https://github.com/rerowep))
- data: update JSON schema to draft 07 [\#862](https://github.com/rero/rero-ils/pull/862) ([BadrAly](https://github.com/BadrAly))
- api: test existence of pid's [\#853](https://github.com/rero/rero-ils/pull/853) ([rerowep](https://github.com/rerowep))
- Paging \(stack request\) functionnalities [\#708](https://github.com/rero/rero-ils/pull/708) ([zannkukai](https://github.com/zannkukai))
- document: delete link to item detail view [\#1011](https://github.com/rero/rero-ils/pull/1011) ([zannkukai](https://github.com/zannkukai))
- release: v0.9.0 [\#1009](https://github.com/rero/rero-ils/pull/1009) ([iGormilhit](https://github.com/iGormilhit))
- v0.9.0 translations [\#998](https://github.com/rero/rero-ils/pull/998) ([iGormilhit](https://github.com/iGormilhit))
- translations: add translations API [\#997](https://github.com/rero/rero-ils/pull/997) ([jma](https://github.com/jma))
- persons: link persons to source instead of MEF [\#996](https://github.com/rero/rero-ils/pull/996) ([rerowep](https://github.com/rerowep))
- documentation: add an actual README to the project [\#995](https://github.com/rero/rero-ils/pull/995) ([iGormilhit](https://github.com/iGormilhit))
- Permissions : Refactoring permissions usage [\#985](https://github.com/rero/rero-ils/pull/985) ([zannkukai](https://github.com/zannkukai))
- ebooks: fix holdings update when importing ebooks [\#984](https://github.com/rero/rero-ils/pull/984) ([rerowep](https://github.com/rerowep))
- US1305 data model illustrations colors physical details [\#980](https://github.com/rero/rero-ils/pull/980) ([rerowep](https://github.com/rerowep))
- celery: redis scheduler backend [\#974](https://github.com/rero/rero-ils/pull/974) ([rerowep](https://github.com/rerowep))
- patron: add blocking functionnality [\#902](https://github.com/rero/rero-ils/pull/902) ([blankoworld](https://github.com/blankoworld))
- tests: implement first tests with cypress [\#878](https://github.com/rero/rero-ils/pull/878) ([AoNoOokami](https://github.com/AoNoOokami))

## [v0.8.0](https://github.com/rero/rero-ils/tree/v0.8.0) (2020-05-05)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.7.0...v0.8.0)

**Implemented enhancements:**

- Use library email address when sending a notification [\#939](https://github.com/rero/rero-ils/issues/939)

**Fixed bugs:**

- Delete disabled button doesn't allow to show reasons not to delete [\#945](https://github.com/rero/rero-ils/issues/945)

**Closed issues:**

- persons does not appears in the autocomplete search input [\#964](https://github.com/rero/rero-ils/issues/964)
- pickup location is not updated in item detail view using Chrome [\#960](https://github.com/rero/rero-ils/issues/960)
- Initial Update [\#923](https://github.com/rero/rero-ils/issues/923)
- Briew view display bug when quickly clicking from tab to tab [\#901](https://github.com/rero/rero-ils/issues/901)
- document : staff can't indicate an eISBN or an eISSN as identifier [\#895](https://github.com/rero/rero-ils/issues/895)
- Autocomplete results not displayed, click in the input needed [\#788](https://github.com/rero/rero-ils/issues/788)
- Location URI are not filtered by library for a system librarian [\#697](https://github.com/rero/rero-ils/issues/697)
- display of qualifier for persons in RERO ILS [\#657](https://github.com/rero/rero-ils/issues/657)
- Changes of communication language for patrons are effective but not displayed [\#583](https://github.com/rero/rero-ils/issues/583)
- Jean-Paul II \(GND\) not in MEF anymore [\#555](https://github.com/rero/rero-ils/issues/555)
- Journal/giornale appears as "Città" in facet document type [\#529](https://github.com/rero/rero-ils/issues/529)

**Merged pull requests:**

- translation: update translations, improve schema [\#967](https://github.com/rero/rero-ils/pull/967) ([iGormilhit](https://github.com/iGormilhit))
- release: v0.8.0 [\#966](https://github.com/rero/rero-ils/pull/966) ([iGormilhit](https://github.com/iGormilhit))
- documentation: add dependencies in PR template [\#963](https://github.com/rero/rero-ils/pull/963) ([iGormilhit](https://github.com/iGormilhit))
- permission: fix organisation permission [\#957](https://github.com/rero/rero-ils/pull/957) ([zannkukai](https://github.com/zannkukai))
- publication pattern: create a manual prediction [\#952](https://github.com/rero/rero-ils/pull/952) ([jma](https://github.com/jma))
- notification: use pickup location email as sender [\#950](https://github.com/rero/rero-ils/pull/950) ([rerowep](https://github.com/rerowep))
- Us1293 doo invenio32 [\#949](https://github.com/rero/rero-ils/pull/949) ([jma](https://github.com/jma))
- test: fix external ones [\#946](https://github.com/rero/rero-ils/pull/946) ([blankoworld](https://github.com/blankoworld))
- test: fix run-test [\#942](https://github.com/rero/rero-ils/pull/942) ([rerowep](https://github.com/rerowep))
- Merge "Subscription" branch to dev [\#940](https://github.com/rero/rero-ils/pull/940) ([zannkukai](https://github.com/zannkukai))
- setup: fix ref. prob. on responsibilityStatement [\#938](https://github.com/rero/rero-ils/pull/938) ([blankoworld](https://github.com/blankoworld))
- tests: fix pytest-invenio static path location [\#937](https://github.com/rero/rero-ils/pull/937) ([jma](https://github.com/jma))
- loan: update request pickup location [\#935](https://github.com/rero/rero-ils/pull/935) ([AoNoOokami](https://github.com/AoNoOokami))
- notification: use responsibility statement [\#926](https://github.com/rero/rero-ils/pull/926) ([rerowep](https://github.com/rerowep))
- test: safety check [\#924](https://github.com/rero/rero-ils/pull/924) ([rerowep](https://github.com/rerowep))
- fault save ebook harvesting [\#922](https://github.com/rero/rero-ils/pull/922) ([rerowep](https://github.com/rerowep))
- location: add test to increase code coverage [\#919](https://github.com/rero/rero-ils/pull/919) ([zannkukai](https://github.com/zannkukai))
- Translate '/rero\_ils/translations/messages.pot' in 'it' [\#912](https://github.com/rero/rero-ils/pull/912) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- permissions: update permission API and configuration [\#893](https://github.com/rero/rero-ils/pull/893) ([zannkukai](https://github.com/zannkukai))
- document: adapt serializer to filter by org in admin view [\#852](https://github.com/rero/rero-ils/pull/852) ([AoNoOokami](https://github.com/AoNoOokami))

## [v0.7.0](https://github.com/rero/rero-ils/tree/v0.7.0) (2020-04-10)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.6.1...v0.7.0)

**Implemented enhancements:**

- Browsing during setup [\#869](https://github.com/rero/rero-ils/issues/869)
- Notification: responsibility statement instead of author [\#406](https://github.com/rero/rero-ils/issues/406)

**Closed issues:**

- Display original alphabet first [\#876](https://github.com/rero/rero-ils/issues/876)
- Action menu for fees [\#871](https://github.com/rero/rero-ils/issues/871)
- Bootstrap: attempt to install TGZ\_FILE even if no option in command line [\#856](https://github.com/rero/rero-ils/issues/856)
- Creation of different record with same pid possible [\#850](https://github.com/rero/rero-ils/issues/850)
- Not possible to create some of the loan fixtures [\#838](https://github.com/rero/rero-ils/issues/838)
- Space after pickup location name [\#830](https://github.com/rero/rero-ils/issues/830)
- Flash message for checkin with fees, requests or transit [\#829](https://github.com/rero/rero-ils/issues/829)
- Alignment of checkins and checkouts infos [\#827](https://github.com/rero/rero-ils/issues/827)
- Validation message "Record Created with pid" [\#805](https://github.com/rero/rero-ils/issues/805)
- Focus set in the list of requests to validate [\#803](https://github.com/rero/rero-ils/issues/803)
- Item detailed view: missing circulation info [\#798](https://github.com/rero/rero-ils/issues/798)
- Pickup name of location must be required [\#794](https://github.com/rero/rero-ils/issues/794)
- Patron to display in the checkin form [\#793](https://github.com/rero/rero-ils/issues/793)
- Authorisations [\#787](https://github.com/rero/rero-ils/issues/787)
- Location settings aren't explained in the editor and an online pickup location is possible [\#604](https://github.com/rero/rero-ils/issues/604)
- Protect the library custom editor [\#575](https://github.com/rero/rero-ils/issues/575)

**Merged pull requests:**

- Translate '/rero\_ils/translations/messages.pot' in 'nl' [\#904](https://github.com/rero/rero-ils/pull/904) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- Translate '/rero\_ils/translations/messages.pot' in 'es' [\#900](https://github.com/rero/rero-ils/pull/900) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- Translate '/rero\_ils/translations/messages.pot' in 'it' [\#897](https://github.com/rero/rero-ils/pull/897) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- git: integrate US1232 into dev [\#896](https://github.com/rero/rero-ils/pull/896) ([reropag](https://github.com/reropag))
- Translate '/rero\_ils/translations/messages.pot' in 'ar' [\#892](https://github.com/rero/rero-ils/pull/892) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- security: fix bleach ReDOS security breach [\#872](https://github.com/rero/rero-ils/pull/872) ([blankoworld](https://github.com/blankoworld))
- acquisition: cleanup useless functions of order lines resource [\#867](https://github.com/rero/rero-ils/pull/867) ([lauren-d](https://github.com/lauren-d))
- vulnerability: fix PyYaml CVE vulnerability [\#866](https://github.com/rero/rero-ils/pull/866) ([blankoworld](https://github.com/blankoworld))
- project: improve test on dates [\#863](https://github.com/rero/rero-ils/pull/863) ([blankoworld](https://github.com/blankoworld))
- test: fix library opening timezone due date [\#859](https://github.com/rero/rero-ils/pull/859) ([blankoworld](https://github.com/blankoworld))
- data: fix location data problem [\#858](https://github.com/rero/rero-ils/pull/858) ([zannkukai](https://github.com/zannkukai))
- bootstrap: fix useless tgz file installation [\#857](https://github.com/rero/rero-ils/pull/857) ([blankoworld](https://github.com/blankoworld))
- security: fix bleach XSS security breach [\#854](https://github.com/rero/rero-ils/pull/854) ([blankoworld](https://github.com/blankoworld))
- document: fix cover image in public detailed view [\#848](https://github.com/rero/rero-ils/pull/848) ([AoNoOokami](https://github.com/AoNoOokami))
- tests: fix Zürich timezone problems [\#847](https://github.com/rero/rero-ils/pull/847) ([blankoworld](https://github.com/blankoworld))
- db: fix sequence indentifier [\#846](https://github.com/rero/rero-ils/pull/846) ([rerowep](https://github.com/rerowep))
- request: fix request made by a librarian [\#843](https://github.com/rero/rero-ils/pull/843) ([AoNoOokami](https://github.com/AoNoOokami))
- location: adapt JSON schema for pickup\_name required if is\_pickup [\#842](https://github.com/rero/rero-ils/pull/842) ([zannkukai](https://github.com/zannkukai))
- installation: fix python packages dependencies [\#841](https://github.com/rero/rero-ils/pull/841) ([jma](https://github.com/jma))
- tests: fix dependencies and security check [\#839](https://github.com/rero/rero-ils/pull/839) ([jma](https://github.com/jma))
- patron\_transaction: adapt features after PO testing [\#837](https://github.com/rero/rero-ils/pull/837) ([zannkukai](https://github.com/zannkukai))
- tests: fix problems with daylight saving time [\#836](https://github.com/rero/rero-ils/pull/836) ([blankoworld](https://github.com/blankoworld))
- monitoring: monitoring for DB and ES [\#833](https://github.com/rero/rero-ils/pull/833) ([rerowep](https://github.com/rerowep))
- circulation: return all applied actions after a checkin or checkout [\#824](https://github.com/rero/rero-ils/pull/824) ([BadrAly](https://github.com/BadrAly))
- Transform "Fees" to "PatronTransaction" data model [\#820](https://github.com/rero/rero-ils/pull/820) ([zannkukai](https://github.com/zannkukai))
- documentation: update INSTALL.rst [\#818](https://github.com/rero/rero-ils/pull/818) ([AoNoOokami](https://github.com/AoNoOokami))
- patron editor: add placeholders [\#815](https://github.com/rero/rero-ils/pull/815) ([AoNoOokami](https://github.com/AoNoOokami))
- release: update changes & release notes for v0.6.0 and v0.6.1 [\#812](https://github.com/rero/rero-ils/pull/812) ([iGormilhit](https://github.com/iGormilhit))
- serials: introduce serials patterns and captions [\#810](https://github.com/rero/rero-ils/pull/810) ([BadrAly](https://github.com/BadrAly))
- public interface: improve patron request deletion [\#808](https://github.com/rero/rero-ils/pull/808) ([AoNoOokami](https://github.com/AoNoOokami))
- metadata: electronicLocator [\#761](https://github.com/rero/rero-ils/pull/761) ([rerowep](https://github.com/rerowep))
- documentation: Flask-Wiki integration [\#740](https://github.com/rero/rero-ils/pull/740) ([jma](https://github.com/jma))
- acquisition: create invoice resource [\#729](https://github.com/rero/rero-ils/pull/729) ([lauren-d](https://github.com/lauren-d))
- documentation: update release notes and changelog [\#920](https://github.com/rero/rero-ils/pull/920) ([iGormilhit](https://github.com/iGormilhit))
- ui: move to rero-ils-ui v0.1.0 [\#915](https://github.com/rero/rero-ils/pull/915) ([jma](https://github.com/jma))
- location: correct schema to work well with formly [\#914](https://github.com/rero/rero-ils/pull/914) ([zannkukai](https://github.com/zannkukai))
- project: fix sqlalchemy last releases problems [\#910](https://github.com/rero/rero-ils/pull/910) ([blankoworld](https://github.com/blankoworld))
- translation: fix key source issues [\#909](https://github.com/rero/rero-ils/pull/909) ([iGormilhit](https://github.com/iGormilhit))
- Translate '/rero\_ils/translations/messages.pot' in 'en' [\#908](https://github.com/rero/rero-ils/pull/908) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- fixture: recreation of documents for MEF [\#889](https://github.com/rero/rero-ils/pull/889) ([rerowep](https://github.com/rerowep))
- issues: trim item and patron barcodes [\#887](https://github.com/rero/rero-ils/pull/887) ([BadrAly](https://github.com/BadrAly))

## [v0.6.1](https://github.com/rero/rero-ils/tree/v0.6.1) (2020-03-02)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.6.0...v0.6.1)

**Implemented enhancements:**

- Helping examples to fill in the patron registration form [\#538](https://github.com/rero/rero-ils/issues/538)

**Closed issues:**

- Name of the patron who made the request [\#826](https://github.com/rero/rero-ils/issues/826)
- Adapt request to validate to the library switch [\#817](https://github.com/rero/rero-ils/issues/817)
- Placeholder in patron form [\#804](https://github.com/rero/rero-ils/issues/804)
- Missing translations: patron editor [\#572](https://github.com/rero/rero-ils/issues/572)

**Merged pull requests:**

- ui: move to rero-ils-ui 0.0.12 [\#823](https://github.com/rero/rero-ils/pull/823) ([jma](https://github.com/jma))
- Translate '/rero\_ils/translations/messages.pot' in 'nl' [\#814](https://github.com/rero/rero-ils/pull/814) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- cli: fix typo [\#811](https://github.com/rero/rero-ils/pull/811) ([lauren-d](https://github.com/lauren-d))

## [v0.6.0](https://github.com/rero/rero-ils/tree/v0.6.0) (2020-02-26)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.5.2...v0.6.0)

**Implemented enhancements:**

- Display Popup for a checkin operation if item are in transit [\#783](https://github.com/rero/rero-ils/issues/783)
- Better menus [\#483](https://github.com/rero/rero-ils/issues/483)
- Validation of Circulation policy settings [\#213](https://github.com/rero/rero-ils/issues/213)
- global Provider [\#106](https://github.com/rero/rero-ils/issues/106)
- print\(e\) [\#86](https://github.com/rero/rero-ils/issues/86)

**Closed issues:**

- Display of "No loan for the current patron" [\#799](https://github.com/rero/rero-ils/issues/799)
- Display action realised in checkin form [\#792](https://github.com/rero/rero-ils/issues/792)
- Message to be displayed as checking out an item requested by another patron [\#791](https://github.com/rero/rero-ils/issues/791)
- Circulation UI: missing space between first and last name [\#790](https://github.com/rero/rero-ils/issues/790)
- Circulation: trim barcode [\#789](https://github.com/rero/rero-ils/issues/789)
- Short fixture correction Wang \> Wang [\#695](https://github.com/rero/rero-ils/issues/695)
- Facets order should be consistent through global and organisations views [\#688](https://github.com/rero/rero-ils/issues/688)
- Flash messages should always start with a capitalized initial. [\#661](https://github.com/rero/rero-ils/issues/661)
- missing mapping in JSON files [\#649](https://github.com/rero/rero-ils/issues/649)
- Wrong french traduction of "System librarian" on the homepage of ils.test.rero.ch [\#646](https://github.com/rero/rero-ils/issues/646)
- Irma is not able to open the circulation policy editor [\#626](https://github.com/rero/rero-ils/issues/626)
- Circulation policy custom editor do not load patron types and item types settings [\#625](https://github.com/rero/rero-ils/issues/625)
- Item type with name "Standard" [\#624](https://github.com/rero/rero-ils/issues/624)
- Add locations to other libraries [\#622](https://github.com/rero/rero-ils/issues/622)
- Validation messages should be set in the form options [\#605](https://github.com/rero/rero-ils/issues/605)
- Indexing : Deleting 'mef\_persons' cause 'index\_not\_found' exception  [\#601](https://github.com/rero/rero-ils/issues/601)
- A librarian of organisation A is allowed to checkout an item of organisation B [\#600](https://github.com/rero/rero-ils/issues/600)
- Due date according to opening hours not working [\#599](https://github.com/rero/rero-ils/issues/599)
- New/edit patron required field validation [\#584](https://github.com/rero/rero-ils/issues/584)
- Suppression of a document: no confirmation [\#552](https://github.com/rero/rero-ils/issues/552)
- Persons aren't filtered by views [\#550](https://github.com/rero/rero-ils/issues/550)
- Missing create button for the first record of a given resource [\#541](https://github.com/rero/rero-ils/issues/541)
- Missing space between the check boxes and the titles of the roles in the patron registration form [\#539](https://github.com/rero/rero-ils/issues/539)
- Authors facets does not appear on public search view [\#372](https://github.com/rero/rero-ils/issues/372)
- Opening hours editor page has to be refreshed to display changes [\#337](https://github.com/rero/rero-ils/issues/337)
- Search autocomplete in jinja detailed views. [\#242](https://github.com/rero/rero-ils/issues/242)
- Checkin of item with requests: in transit to wrong library [\#780](https://github.com/rero/rero-ils/issues/780)
- Select pickup locations instead of library name [\#777](https://github.com/rero/rero-ils/issues/777)
- Library code displayed in the holding [\#776](https://github.com/rero/rero-ils/issues/776)
- Requests to validate by library switching [\#775](https://github.com/rero/rero-ils/issues/775)
- Wrong locations proposed in the item editor [\#772](https://github.com/rero/rero-ils/issues/772)
- Impossible to create a user with role "librarian" [\#771](https://github.com/rero/rero-ils/issues/771)
- In transit to: destination not displayed [\#770](https://github.com/rero/rero-ils/issues/770)
- In transit to: display library name [\#769](https://github.com/rero/rero-ils/issues/769)

**Merged pull requests:**

- ui: move to rero-ils-ui 0.0.11 [\#809](https://github.com/rero/rero-ils/pull/809) ([jma](https://github.com/jma))
- isort: fix isort problems for two files [\#807](https://github.com/rero/rero-ils/pull/807) ([BadrAly](https://github.com/BadrAly))
- Translate '/rero\_ils/translations/messages.pot' in 'es' [\#796](https://github.com/rero/rero-ils/pull/796) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- Translate '/rero\_ils/translations/messages.pot' in 'ar' [\#785](https://github.com/rero/rero-ils/pull/785) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- data: correction on users data [\#781](https://github.com/rero/rero-ils/pull/781) ([zannkukai](https://github.com/zannkukai))
- items: fix automatic checkin return informations [\#774](https://github.com/rero/rero-ils/pull/774) ([zannkukai](https://github.com/zannkukai))
- utils: $ref from pid [\#765](https://github.com/rero/rero-ils/pull/765) ([rerowep](https://github.com/rerowep))
- Translate '/rero\_ils/translations/messages.pot' in 'de' [\#763](https://github.com/rero/rero-ils/pull/763) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- translation: fix error with translation file [\#762](https://github.com/rero/rero-ils/pull/762) ([BadrAly](https://github.com/BadrAly))
- Translate '/rero\_ils/translations/messages.pot' in 'es' [\#759](https://github.com/rero/rero-ils/pull/759) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- Translate '/rero\_ils/translations/messages.pot' in 'en' [\#758](https://github.com/rero/rero-ils/pull/758) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- Translate '/rero\_ils/translations/messages.pot' in 'fr' [\#757](https://github.com/rero/rero-ils/pull/757) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- public interface: request deletion by patron [\#756](https://github.com/rero/rero-ils/pull/756) ([AoNoOokami](https://github.com/AoNoOokami))
- Translate '/rero\_ils/translations/messages.pot' in 'es' [\#750](https://github.com/rero/rero-ils/pull/750) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- Translate '/rero\_ils/translations/messages.pot' in 'en' [\#748](https://github.com/rero/rero-ils/pull/748) ([transifex-integration[bot]](https://github.com/apps/transifex-integration))
- tests: fix travis failed with werkzeug==1.0.0 [\#747](https://github.com/rero/rero-ils/pull/747) ([jma](https://github.com/jma))
- documentation: complete authors page [\#745](https://github.com/rero/rero-ils/pull/745) ([blankoworld](https://github.com/blankoworld))
- acq\_account: disable account deletion when it has orders linked to it. [\#737](https://github.com/rero/rero-ils/pull/737) ([BadrAly](https://github.com/BadrAly))
- improve bnf import [\#733](https://github.com/rero/rero-ils/pull/733) ([rerowep](https://github.com/rerowep))
- config: add default sort on resources [\#731](https://github.com/rero/rero-ils/pull/731) ([Garfield-fr](https://github.com/Garfield-fr))
- editor: fix "required status" error in item editor [\#728](https://github.com/rero/rero-ils/pull/728) ([AoNoOokami](https://github.com/AoNoOokami))
- item: add field location on form configuration [\#727](https://github.com/rero/rero-ils/pull/727) ([Garfield-fr](https://github.com/Garfield-fr))
- ui: Search input takes now all the header area [\#724](https://github.com/rero/rero-ils/pull/724) ([blankoworld](https://github.com/blankoworld))
- doc: create reroils resource diagram to show relations [\#722](https://github.com/rero/rero-ils/pull/722) ([BadrAly](https://github.com/BadrAly))
- data: preload persons and export [\#721](https://github.com/rero/rero-ils/pull/721) ([rerowep](https://github.com/rerowep))
- acquisition: link order line to a document [\#719](https://github.com/rero/rero-ils/pull/719) ([lauren-d](https://github.com/lauren-d))
- US813 [\#714](https://github.com/rero/rero-ils/pull/714) ([BadrAly](https://github.com/BadrAly))
- indexer: fix person indexing [\#711](https://github.com/rero/rero-ils/pull/711) ([rerowep](https://github.com/rerowep))
- Acquisition [\#709](https://github.com/rero/rero-ils/pull/709) ([iGormilhit](https://github.com/iGormilhit))
- ui: display a different logo/color for each orga. [\#706](https://github.com/rero/rero-ils/pull/706) ([blankoworld](https://github.com/blankoworld))
- ES: fix mapping [\#705](https://github.com/rero/rero-ils/pull/705) ([rerowep](https://github.com/rerowep))
- tests: fix run-test [\#702](https://github.com/rero/rero-ils/pull/702) ([rerowep](https://github.com/rerowep))
- deployment: adaptions for rero-ils-ui [\#700](https://github.com/rero/rero-ils/pull/700) ([rerowep](https://github.com/rerowep))
- setup: speed up and clean improvements [\#699](https://github.com/rero/rero-ils/pull/699) ([blankoworld](https://github.com/blankoworld))
- script: add rero-ils-ui install from tgz [\#692](https://github.com/rero/rero-ils/pull/692) ([AoNoOokami](https://github.com/AoNoOokami))
- editor: move to ngx-formly [\#690](https://github.com/rero/rero-ils/pull/690) ([jma](https://github.com/jma))
- loans: improve due date timezone consideration [\#684](https://github.com/rero/rero-ils/pull/684) ([blankoworld](https://github.com/blankoworld))
- libraries: add sort by name configuration [\#681](https://github.com/rero/rero-ils/pull/681) ([Garfield-fr](https://github.com/Garfield-fr))
- cli: fixture pid dependency test with config file [\#679](https://github.com/rero/rero-ils/pull/679) ([rerowep](https://github.com/rerowep))
- scripts: fix objects indexation [\#678](https://github.com/rero/rero-ils/pull/678) ([blankoworld](https://github.com/blankoworld))
- person: filter by view … [\#676](https://github.com/rero/rero-ils/pull/676) ([AoNoOokami](https://github.com/AoNoOokami))
- filter persons view [\#674](https://github.com/rero/rero-ils/pull/674) ([rerowep](https://github.com/rerowep))
- circulation policy: ignore settings when deleting a policy [\#672](https://github.com/rero/rero-ils/pull/672) ([BadrAly](https://github.com/BadrAly))
- cli: pid fixture dependencies [\#667](https://github.com/rero/rero-ils/pull/667) ([rerowep](https://github.com/rerowep))
- translation: fix patron form editor translation problem [\#666](https://github.com/rero/rero-ils/pull/666) ([zannkukai](https://github.com/zannkukai))
- data: rewrite provisionActivity field [\#663](https://github.com/rero/rero-ils/pull/663) ([rerowep](https://github.com/rerowep))
- ui: add switch to professional view [\#662](https://github.com/rero/rero-ils/pull/662) ([AoNoOokami](https://github.com/AoNoOokami))
- serializer: remove \_settings key on aggregations [\#660](https://github.com/rero/rero-ils/pull/660) ([Garfield-fr](https://github.com/Garfield-fr))
- 1182 - improve perf with MEF [\#659](https://github.com/rero/rero-ils/pull/659) ([blankoworld](https://github.com/blankoworld))
- deployment: fix pipenv version [\#658](https://github.com/rero/rero-ils/pull/658) ([rerowep](https://github.com/rerowep))
- translation: edition & responsability [\#656](https://github.com/rero/rero-ils/pull/656) ([rerowep](https://github.com/rerowep))
- travis: fix errors [\#655](https://github.com/rero/rero-ils/pull/655) ([rerowep](https://github.com/rerowep))
- fixtures: change library opening hours for organisation 3 [\#654](https://github.com/rero/rero-ils/pull/654) ([Garfield-fr](https://github.com/Garfield-fr))
- Us986 admin [\#652](https://github.com/rero/rero-ils/pull/652) ([jma](https://github.com/jma))
- data model: implement edition statement transformation [\#651](https://github.com/rero/rero-ils/pull/651) ([rerowep](https://github.com/rerowep))
- ui: correct frontpage typo [\#647](https://github.com/rero/rero-ils/pull/647) ([AoNoOokami](https://github.com/AoNoOokami))
- frontend: remove admin actions [\#645](https://github.com/rero/rero-ils/pull/645) ([Garfield-fr](https://github.com/Garfield-fr))
- circulation policies: fix settings bug [\#644](https://github.com/rero/rero-ils/pull/644) ([Garfield-fr](https://github.com/Garfield-fr))
- cli: add new translate command [\#643](https://github.com/rero/rero-ils/pull/643) ([rerowep](https://github.com/rerowep))
- tests: improve test coverage [\#640](https://github.com/rero/rero-ils/pull/640) ([rerowep](https://github.com/rerowep))
- template: update pr template [\#638](https://github.com/rero/rero-ils/pull/638) ([AoNoOokami](https://github.com/AoNoOokami))
- setup: lazy creation of records [\#635](https://github.com/rero/rero-ils/pull/635) ([rerowep](https://github.com/rerowep))
- items: create items dump functionality [\#634](https://github.com/rero/rero-ils/pull/634) ([BadrAly](https://github.com/BadrAly))
- fix: correct circulation policy [\#633](https://github.com/rero/rero-ils/pull/633) ([AoNoOokami](https://github.com/AoNoOokami))
- permissions: allow read access to holding and items for all users [\#632](https://github.com/rero/rero-ils/pull/632) ([BadrAly](https://github.com/BadrAly))
- documents: fix document suppression problems [\#631](https://github.com/rero/rero-ils/pull/631) ([zannkukai](https://github.com/zannkukai))
- ebooks: fix ebooks dojson [\#628](https://github.com/rero/rero-ils/pull/628) ([rerowep](https://github.com/rerowep))
- data: Adds dump for documents [\#618](https://github.com/rero/rero-ils/pull/618) ([rerowep](https://github.com/rerowep))
- renewals: add renew buttons for patrons checked-out items [\#610](https://github.com/rero/rero-ils/pull/610) ([BadrAly](https://github.com/BadrAly))
- scripts: add info message coloration [\#564](https://github.com/rero/rero-ils/pull/564) ([blankoworld](https://github.com/blankoworld))
- circulation: fix some loan scenarios [\#806](https://github.com/rero/rero-ils/pull/806) ([BadrAly](https://github.com/BadrAly))
- circulation: fix item status after a check-in [\#782](https://github.com/rero/rero-ils/pull/782) ([BadrAly](https://github.com/BadrAly))
- documents: Add pickup location names for the item request button [\#779](https://github.com/rero/rero-ils/pull/779) ([zannkukai](https://github.com/zannkukai))
- ui: display library name instead of code [\#778](https://github.com/rero/rero-ils/pull/778) ([jma](https://github.com/jma))
- security: authorize unsafe-eval param on script-src [\#773](https://github.com/rero/rero-ils/pull/773) ([Garfield-fr](https://github.com/Garfield-fr))
- ebooks: fix ebook import indexing [\#768](https://github.com/rero/rero-ils/pull/768) ([rerowep](https://github.com/rerowep))
- config: allow loading external script [\#767](https://github.com/rero/rero-ils/pull/767) ([Garfield-fr](https://github.com/Garfield-fr))
- config: allow loading inline image in the security configuration [\#766](https://github.com/rero/rero-ils/pull/766) ([Garfield-fr](https://github.com/Garfield-fr))
- release: v0.6.0 [\#764](https://github.com/rero/rero-ils/pull/764) ([iGormilhit](https://github.com/iGormilhit))
- permissions: update and delete permissions api for records [\#760](https://github.com/rero/rero-ils/pull/760) ([BadrAly](https://github.com/BadrAly))
- documents: update schemas about abstract field [\#754](https://github.com/rero/rero-ils/pull/754) ([zannkukai](https://github.com/zannkukai))
- ui: move to rero-ils-ui@0.0.10 [\#752](https://github.com/rero/rero-ils/pull/752) ([jma](https://github.com/jma))
- circulation: correct pickup location for actions [\#749](https://github.com/rero/rero-ils/pull/749) ([AoNoOokami](https://github.com/AoNoOokami))
- data model: fix jsonschema for the editor [\#746](https://github.com/rero/rero-ils/pull/746) ([jma](https://github.com/jma))
- homepage: add homepage informations for pilot instance [\#744](https://github.com/rero/rero-ils/pull/744) ([Garfield-fr](https://github.com/Garfield-fr))
- ES: fix listeners [\#738](https://github.com/rero/rero-ils/pull/738) ([rerowep](https://github.com/rerowep))
- patrons: display checkout history for patron [\#720](https://github.com/rero/rero-ils/pull/720) ([BadrAly](https://github.com/BadrAly))

## [v0.5.2](https://github.com/rero/rero-ils/tree/v0.5.2) (2019-11-13)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.5.1...v0.5.2)

**Closed issues:**

- Requesting an item from another organisation should not be possible [\#619](https://github.com/rero/rero-ils/issues/619)
- Document editor: if all authors are removed from the form, then it's not possible to add an author [\#609](https://github.com/rero/rero-ils/issues/609)
- Patron creation by a librarian: reset password link never works [\#608](https://github.com/rero/rero-ils/issues/608)
- Import document from BnF not working [\#607](https://github.com/rero/rero-ils/issues/607)
- Attaching an item to an harvested ebook should not be possible [\#603](https://github.com/rero/rero-ils/issues/603)
- Render a document detailed view with document even if there's a library without pickup location in the organisation [\#598](https://github.com/rero/rero-ils/issues/598)
- "Non extendable" not translated in notification [\#571](https://github.com/rero/rero-ils/issues/571)
- Fees: API returns 0 records  [\#560](https://github.com/rero/rero-ils/issues/560)

**Merged pull requests:**

- dojson: fix provisionActivity unimarc transformation [\#623](https://github.com/rero/rero-ils/pull/623) ([jma](https://github.com/jma))
- Workshop Issues Fixing [\#614](https://github.com/rero/rero-ils/pull/614) ([jma](https://github.com/jma))

## [v0.5.1](https://github.com/rero/rero-ils/tree/v0.5.1) (2019-11-05)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.5.0...v0.5.1)

**Implemented enhancements:**

- Flash message: bring user at top of the page [\#232](https://github.com/rero/rero-ils/issues/232)

**Closed issues:**

- Librarian can edit items from other libraries [\#574](https://github.com/rero/rero-ils/issues/574)
- "online" item type in fixture [\#573](https://github.com/rero/rero-ils/issues/573)
- database sequences are not updated after executing script/setup  [\#563](https://github.com/rero/rero-ils/issues/563)
- Not possible to add or edit a location if field is\_online is not checked [\#562](https://github.com/rero/rero-ils/issues/562)
- Editor: qualifier vs. note [\#557](https://github.com/rero/rero-ils/issues/557)
- Document editor: save button disabled [\#556](https://github.com/rero/rero-ils/issues/556)
- Facet author not always displayed \(in Firefox\) [\#554](https://github.com/rero/rero-ils/issues/554)
- Person page: no links to documents in organisation views [\#553](https://github.com/rero/rero-ils/issues/553)
- Translation "The item has been requested" [\#404](https://github.com/rero/rero-ils/issues/404)
- Wrong organisation when adding item or patron types [\#389](https://github.com/rero/rero-ils/issues/389)
- Fix circ policies editor  [\#363](https://github.com/rero/rero-ils/issues/363)

**Merged pull requests:**

- documentation: update changes and release notes [\#596](https://github.com/rero/rero-ils/pull/596) ([iGormilhit](https://github.com/iGormilhit))
- translations: update missing translations [\#594](https://github.com/rero/rero-ils/pull/594) ([jma](https://github.com/jma))
- ui: fix typeahead unexpected behaviour [\#593](https://github.com/rero/rero-ils/pull/593) ([jma](https://github.com/jma))
- editor: fix location editor button validation [\#592](https://github.com/rero/rero-ils/pull/592) ([lauren-d](https://github.com/lauren-d))
- translation: fix user message when an item is requested [\#591](https://github.com/rero/rero-ils/pull/591) ([zannkukai](https://github.com/zannkukai))
- editor: fix editor button validation [\#590](https://github.com/rero/rero-ils/pull/590) ([lauren-d](https://github.com/lauren-d))
- persons: fix filter to get documents in organisation views [\#589](https://github.com/rero/rero-ils/pull/589) ([benerken](https://github.com/benerken))
- fees: add organisation search filter [\#588](https://github.com/rero/rero-ils/pull/588) ([lauren-d](https://github.com/lauren-d))
- ui: fix flash messages position [\#587](https://github.com/rero/rero-ils/pull/587) ([zannkukai](https://github.com/zannkukai))
- fixtures: update third organisation circulation policy [\#586](https://github.com/rero/rero-ils/pull/586) ([iGormilhit](https://github.com/iGormilhit))
- ui: adapt frontpage for mobile devices [\#585](https://github.com/rero/rero-ils/pull/585) ([AoNoOokami](https://github.com/AoNoOokami))
- github: add new info on github issue template [\#581](https://github.com/rero/rero-ils/pull/581) ([blankoworld](https://github.com/blankoworld))
- items: fix online locations status [\#580](https://github.com/rero/rero-ils/pull/580) ([zannkukai](https://github.com/zannkukai))
- translation: correct organisation translation [\#578](https://github.com/rero/rero-ils/pull/578) ([AoNoOokami](https://github.com/AoNoOokami))
- ui: fix global homepage [\#570](https://github.com/rero/rero-ils/pull/570) ([AoNoOokami](https://github.com/AoNoOokami))
- ui: add a new URL to change the language [\#569](https://github.com/rero/rero-ils/pull/569) ([jma](https://github.com/jma))
- permissions: disable edit and delete buttons for librarians [\#566](https://github.com/rero/rero-ils/pull/566) ([BadrAly](https://github.com/BadrAly))

## [v0.5.0](https://github.com/rero/rero-ils/tree/v0.5.0) (2019-10-23)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.4.0...v0.5.0)

**Closed issues:**

- JSON export not working [\#547](https://github.com/rero/rero-ils/issues/547)
- Wrong orgnisation translation in the item type editor [\#540](https://github.com/rero/rero-ils/issues/540)
- Internal server error when displaying record [\#501](https://github.com/rero/rero-ils/issues/501)
- A librarian should not be able to edit libraries he/she's not affiliated to. [\#488](https://github.com/rero/rero-ils/issues/488)
- Links to items and documents from circulation UI [\#446](https://github.com/rero/rero-ils/issues/446)
- Check the responsiveness of the front page [\#381](https://github.com/rero/rero-ils/issues/381)
- Wrong availability for item\_type "no checkout" [\#209](https://github.com/rero/rero-ils/issues/209)
- Removing the barcode from a patron leads to an error after "Submit" action [\#37](https://github.com/rero/rero-ils/issues/37)

**Merged pull requests:**

- ils: translates v0.5.0 strings [\#567](https://github.com/rero/rero-ils/pull/567) ([iGormilhit](https://github.com/iGormilhit))
- documentation: fill in changes and release files [\#565](https://github.com/rero/rero-ils/pull/565) ([iGormilhit](https://github.com/iGormilhit))
- fixtures: reset sequence to correct value after loading records [\#561](https://github.com/rero/rero-ils/pull/561) ([BadrAly](https://github.com/BadrAly))
- document: fix json export [\#548](https://github.com/rero/rero-ils/pull/548) ([Garfield-fr](https://github.com/Garfield-fr))
- fixtures: add data for a third organisation [\#543](https://github.com/rero/rero-ils/pull/543) ([iGormilhit](https://github.com/iGormilhit))
- US965: Holdings/items for ebooks [\#537](https://github.com/rero/rero-ils/pull/537) ([Garfield-fr](https://github.com/Garfield-fr))
- \#1021 - refactoring: delete unused imports [\#536](https://github.com/rero/rero-ils/pull/536) ([blankoworld](https://github.com/blankoworld))
- docker: update elasticsearch and kibana to version 6.6.2 [\#534](https://github.com/rero/rero-ils/pull/534) ([Garfield-fr](https://github.com/Garfield-fr))
- US696: overdue fees [\#530](https://github.com/rero/rero-ils/pull/530) ([BadrAly](https://github.com/BadrAly))
- \#971 - ui: display git commit hash on frontpage [\#524](https://github.com/rero/rero-ils/pull/524) ([blankoworld](https://github.com/blankoworld))
- \#1027 - item availability instead of status [\#523](https://github.com/rero/rero-ils/pull/523) ([blankoworld](https://github.com/blankoworld))
- circ\_policies ui: increase API size limit [\#509](https://github.com/rero/rero-ils/pull/509) ([zannkukai](https://github.com/zannkukai))
- \#1019 - Refactoring units testing api calls [\#497](https://github.com/rero/rero-ils/pull/497) ([blankoworld](https://github.com/blankoworld))

## [v0.4.0](https://github.com/rero/rero-ils/tree/v0.4.0) (2019-09-30)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.3.1...v0.4.0)

**Implemented enhancements:**

- Checkin/checkout tab top text [\#366](https://github.com/rero/rero-ils/issues/366)

**Closed issues:**

- Thumbnails detail view [\#495](https://github.com/rero/rero-ils/issues/495)
- Two loans instead of one [\#484](https://github.com/rero/rero-ils/issues/484)
- 2 homepages for global view [\#475](https://github.com/rero/rero-ils/issues/475)
- Checkin of item that should go in transit [\#462](https://github.com/rero/rero-ils/issues/462)
- Mousehover on "Delete", when the item cannot be deleted [\#447](https://github.com/rero/rero-ils/issues/447)
- Availability light in views [\#445](https://github.com/rero/rero-ils/issues/445)
- Detailed view: field "Notes" is displayed with no content [\#437](https://github.com/rero/rero-ils/issues/437)
- Checkout for the end of a day \(23h59\) [\#417](https://github.com/rero/rero-ils/issues/417)
- Layout of confirmation message when deleting an item [\#407](https://github.com/rero/rero-ils/issues/407)
- Increase size of result set during API calls  [\#405](https://github.com/rero/rero-ils/issues/405)
- Merge public and professional document search views. [\#383](https://github.com/rero/rero-ils/issues/383)
- Improve test and test coverage [\#380](https://github.com/rero/rero-ils/issues/380)
- Upgrade to the latest version of invenio-circulation [\#379](https://github.com/rero/rero-ils/issues/379)
- Circulation UI: items & patrons of other organisation [\#377](https://github.com/rero/rero-ils/issues/377)
- Change license headers [\#374](https://github.com/rero/rero-ils/issues/374)
- Display of "My account" [\#225](https://github.com/rero/rero-ils/issues/225)
- UX of date exceptions [\#223](https://github.com/rero/rero-ils/issues/223)
- \[angular\] Handle Error if http client doesn't response [\#167](https://github.com/rero/rero-ils/issues/167)

**Merged pull requests:**

- data: new data files for MEF [\#535](https://github.com/rero/rero-ils/pull/535) ([rerowep](https://github.com/rerowep))
- editor: fix submit button with async validator [\#528](https://github.com/rero/rero-ils/pull/528) ([jma](https://github.com/jma))
- US931 data model publication statement [\#526](https://github.com/rero/rero-ils/pull/526) ([rerowep](https://github.com/rerowep))
- documents: fix language [\#522](https://github.com/rero/rero-ils/pull/522) ([Garfield-fr](https://github.com/Garfield-fr))
- ui: fix front page responsiveness \#381 [\#520](https://github.com/rero/rero-ils/pull/520) ([AoNoOokami](https://github.com/AoNoOokami))
- schema: make the name for publisher optional [\#518](https://github.com/rero/rero-ils/pull/518) ([jma](https://github.com/jma))
- documentation: add a default issue template [\#516](https://github.com/rero/rero-ils/pull/516) ([iGormilhit](https://github.com/iGormilhit))
- tests: fix external tests after availability implementation [\#515](https://github.com/rero/rero-ils/pull/515) ([BadrAly](https://github.com/BadrAly))
- circulation : fix checkin of item that should go in transit [\#512](https://github.com/rero/rero-ils/pull/512) ([benerken](https://github.com/benerken))
- document: fix default icon thumbnail on fullview [\#510](https://github.com/rero/rero-ils/pull/510) ([Garfield-fr](https://github.com/Garfield-fr))
- scripts: wrong command in server script [\#508](https://github.com/rero/rero-ils/pull/508) ([blankoworld](https://github.com/blankoworld))
- \#1036 - bootstrap: delete useless virtualenv [\#506](https://github.com/rero/rero-ils/pull/506) ([blankoworld](https://github.com/blankoworld))
- US911 cataloging [\#504](https://github.com/rero/rero-ils/pull/504) ([jma](https://github.com/jma))
- holdings: display holdings records [\#499](https://github.com/rero/rero-ils/pull/499) ([BadrAly](https://github.com/BadrAly))
- circulation : fix issue two loans instead of one [\#496](https://github.com/rero/rero-ils/pull/496) ([benerken](https://github.com/benerken))
- validate json file with schema [\#493](https://github.com/rero/rero-ils/pull/493) ([rerowep](https://github.com/rerowep))
- US838: display record availability [\#491](https://github.com/rero/rero-ils/pull/491) ([BadrAly](https://github.com/BadrAly))
- \#1011 fix unittest fixtures [\#487](https://github.com/rero/rero-ils/pull/487) ([blankoworld](https://github.com/blankoworld))
- installation: fix bootstrap script to use npm 6 instead of local one [\#481](https://github.com/rero/rero-ils/pull/481) ([blankoworld](https://github.com/blankoworld))
- circulation\_ui: add error logs for item API [\#479](https://github.com/rero/rero-ils/pull/479) ([zannkukai](https://github.com/zannkukai))
- document detailed view: fix missing message on item delete button [\#477](https://github.com/rero/rero-ils/pull/477) ([zannkukai](https://github.com/zannkukai))
- fix user initials view [\#476](https://github.com/rero/rero-ils/pull/476) ([rerowep](https://github.com/rerowep))
- fixtures: generate new files [\#472](https://github.com/rero/rero-ils/pull/472) ([BadrAly](https://github.com/BadrAly))
- global: standardize timezone [\#471](https://github.com/rero/rero-ils/pull/471) ([BadrAly](https://github.com/BadrAly))
- data\_model: implement copyright date transformation [\#470](https://github.com/rero/rero-ils/pull/470) ([reropag](https://github.com/reropag))
- circulation ui: check if item or patron is in same organisation [\#469](https://github.com/rero/rero-ils/pull/469) ([jma](https://github.com/jma))
- circulation ui: enhancement on the text of tab \(checkin/checkout\) [\#465](https://github.com/rero/rero-ils/pull/465) ([Garfield-fr](https://github.com/Garfield-fr))
- libraries date exceptions: fix bug on repeat button [\#463](https://github.com/rero/rero-ils/pull/463) ([Garfield-fr](https://github.com/Garfield-fr))
-  circulation: holdings level adaptation [\#461](https://github.com/rero/rero-ils/pull/461) ([BadrAly](https://github.com/BadrAly))
- US716 holdings level [\#458](https://github.com/rero/rero-ils/pull/458) ([BadrAly](https://github.com/BadrAly))
- oaiharvesting: bulk indexing of oai records [\#456](https://github.com/rero/rero-ils/pull/456) ([rerowep](https://github.com/rerowep))
- tests: test correct licenses in files [\#451](https://github.com/rero/rero-ils/pull/451) ([rerowep](https://github.com/rerowep))
- admin: Wrong organisation on select menu [\#448](https://github.com/rero/rero-ils/pull/448) ([Garfield-fr](https://github.com/Garfield-fr))
- item: fix display of the buttons [\#444](https://github.com/rero/rero-ils/pull/444) ([Garfield-fr](https://github.com/Garfield-fr))
- document: fix notes field [\#441](https://github.com/rero/rero-ils/pull/441) ([Garfield-fr](https://github.com/Garfield-fr))

## [v0.3.1](https://github.com/rero/rero-ils/tree/v0.3.1) (2019-08-26)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.3.0...v0.3.1)

**Merged pull requests:**

- translation: fix missing translated strings [\#459](https://github.com/rero/rero-ils/pull/459) ([iGormilhit](https://github.com/iGormilhit))

## [v0.3.0](https://github.com/rero/rero-ils/tree/v0.3.0) (2019-08-22)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.2.3...v0.3.0)

**Implemented enhancements:**

- Should ebooks records be editable ? [\#89](https://github.com/rero/rero-ils/issues/89)

**Closed issues:**

- Edit item button in professional document search view always visible [\#390](https://github.com/rero/rero-ils/issues/390)
- Search with AND operator does not work as expected. [\#384](https://github.com/rero/rero-ils/issues/384)
- Transaction library instead of item library [\#378](https://github.com/rero/rero-ils/issues/378)
- Search in various fields [\#369](https://github.com/rero/rero-ils/issues/369)
- gnd\_pid / pid [\#352](https://github.com/rero/rero-ils/issues/352)
- \[editor\] location name selector in the item editor [\#348](https://github.com/rero/rero-ils/issues/348)
- Due date in a check-out does not consider closed days introduced in exceptions [\#263](https://github.com/rero/rero-ils/issues/263)

**Merged pull requests:**

- translations: translate v0.3.0 release strings [\#453](https://github.com/rero/rero-ils/pull/453) ([iGormilhit](https://github.com/iGormilhit))
- circulation ui: view code on document and item link [\#452](https://github.com/rero/rero-ils/pull/452) ([Garfield-fr](https://github.com/Garfield-fr))
- tests: fix dependencies on travis [\#450](https://github.com/rero/rero-ils/pull/450) ([jma](https://github.com/jma))
- circulation: due date hours set to end of day [\#449](https://github.com/rero/rero-ils/pull/449) ([Garfield-fr](https://github.com/Garfield-fr))
- notifications: url of the account of the notified patron [\#439](https://github.com/rero/rero-ils/pull/439) ([BadrAly](https://github.com/BadrAly))
- ui: facet language translation [\#438](https://github.com/rero/rero-ils/pull/438) ([Garfield-fr](https://github.com/Garfield-fr))
- circulation: upgrade to invenio-circulation v1.0.0a16 [\#436](https://github.com/rero/rero-ils/pull/436) ([reropag](https://github.com/reropag))
- license: move from GPLv2 to AGPLv3 [\#433](https://github.com/rero/rero-ils/pull/433) ([iGormilhit](https://github.com/iGormilhit))
- data model: language, identifiedBy [\#430](https://github.com/rero/rero-ils/pull/430) ([BadrAly](https://github.com/BadrAly))
- cli: replaces invenio records by invenio fixtures [\#421](https://github.com/rero/rero-ils/pull/421) ([BadrAly](https://github.com/BadrAly))
- ui: Implement global and organisations view [\#419](https://github.com/rero/rero-ils/pull/419) ([Garfield-fr](https://github.com/Garfield-fr))
- ui: fix bad alignment in delete item modal header [\#413](https://github.com/rero/rero-ils/pull/413) ([jma](https://github.com/jma))
- security: update to invenio version 3.1.1 [\#412](https://github.com/rero/rero-ils/pull/412) ([rerowep](https://github.com/rerowep))
- tests: optional execution of external services tests. [\#411](https://github.com/rero/rero-ils/pull/411) ([BadrAly](https://github.com/BadrAly))
- circulation: upgrade to invenio circulation v1.0.0a14 [\#410](https://github.com/rero/rero-ils/pull/410) ([BadrAly](https://github.com/BadrAly))
- indexation class: add indexation property to IlsRecord [\#409](https://github.com/rero/rero-ils/pull/409) ([rerowep](https://github.com/rerowep))
- tests: workaround when bnf service is down [\#403](https://github.com/rero/rero-ils/pull/403) ([BadrAly](https://github.com/BadrAly))
- documentation: update INSTALL.rst [\#402](https://github.com/rero/rero-ils/pull/402) ([vrabe](https://github.com/vrabe))
- search: Replace AND default operator by OR. [\#401](https://github.com/rero/rero-ils/pull/401) ([Garfield-fr](https://github.com/Garfield-fr))
- documentation: add an issue template [\#386](https://github.com/rero/rero-ils/pull/386) ([iGormilhit](https://github.com/iGormilhit))
- documentation: rewrite bad syntax in docstrings [\#382](https://github.com/rero/rero-ils/pull/382) ([iGormilhit](https://github.com/iGormilhit))
- circulation: improve circulation dates [\#375](https://github.com/rero/rero-ils/pull/375) ([BadrAly](https://github.com/BadrAly))
- facets: expand facet items by link [\#364](https://github.com/rero/rero-ils/pull/364) ([Garfield-fr](https://github.com/Garfield-fr))
- notification: create notification templates [\#350](https://github.com/rero/rero-ils/pull/350) ([BadrAly](https://github.com/BadrAly))

## [v0.2.3](https://github.com/rero/rero-ils/tree/v0.2.3) (2019-07-03)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.2.2...v0.2.3)

**Closed issues:**

- TypeError: 'NoneType' object is not iterable [\#367](https://github.com/rero/rero-ils/issues/367)
- Fixtures: write a better and faster way to create circulation transactions  [\#254](https://github.com/rero/rero-ils/issues/254)

**Merged pull requests:**

- fixtures: fix dojson publishers conversion \(3rd time\) [\#373](https://github.com/rero/rero-ils/pull/373) ([iGormilhit](https://github.com/iGormilhit))

## [v0.2.2](https://github.com/rero/rero-ils/tree/v0.2.2) (2019-07-02)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.2.1...v0.2.2)

**Closed issues:**

- Wrong patron displayed when checking in a requested item [\#357](https://github.com/rero/rero-ils/issues/357)
- MultipleLoansOnItemError [\#355](https://github.com/rero/rero-ils/issues/355)

**Merged pull requests:**

- document: Publisher format [\#371](https://github.com/rero/rero-ils/pull/371) ([sebastiendeleze](https://github.com/sebastiendeleze))

## [v0.2.1](https://github.com/rero/rero-ils/tree/v0.2.1) (2019-07-01)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.2.0...v0.2.1)

**Implemented enhancements:**

- Facets: add a "more" link or button. [\#87](https://github.com/rero/rero-ils/issues/87)

**Closed issues:**

- Unnecessary links on ebooks frontpage [\#353](https://github.com/rero/rero-ils/issues/353)
- Space missing in toast message \(only IT and DE\) [\#273](https://github.com/rero/rero-ils/issues/273)
- Patron search doesn't work as expected [\#229](https://github.com/rero/rero-ils/issues/229)

**Merged pull requests:**

- fixture: fix transformation with no publishers [\#368](https://github.com/rero/rero-ils/pull/368) ([iGormilhit](https://github.com/iGormilhit))

## [v0.2.0](https://github.com/rero/rero-ils/tree/v0.2.0) (2019-06-27)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a22...v0.2.0)

**Implemented enhancements:**

- Number of occurrences is wrong in facet "status" [\#10](https://github.com/rero/rero-ils/issues/10)

**Security fixes:**

- Delete on record: check during delete [\#145](https://github.com/rero/rero-ils/issues/145)

**Closed issues:**

- \[UI\] Languages selector [\#349](https://github.com/rero/rero-ils/issues/349)
- Link from person detailed page to document [\#295](https://github.com/rero/rero-ils/issues/295)
- Item location not populated in item editor  [\#217](https://github.com/rero/rero-ils/issues/217)
- Upper and lower case, singular and plural forms [\#119](https://github.com/rero/rero-ils/issues/119)
- Title missing in e-mail sent to patron [\#52](https://github.com/rero/rero-ils/issues/52)

**Merged pull requests:**

- release v0.2.0 [\#362](https://github.com/rero/rero-ils/pull/362) ([iGormilhit](https://github.com/iGormilhit))

## [v0.1.0a22](https://github.com/rero/rero-ils/tree/v0.1.0a22) (2019-05-27)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a21...v0.1.0a22)

**Implemented enhancements:**

- OAI config file loding YAMLLoadWarning [\#304](https://github.com/rero/rero-ils/issues/304)
- Renewal date [\#231](https://github.com/rero/rero-ils/issues/231)
- Check-out of an item "in transit" [\#230](https://github.com/rero/rero-ils/issues/230)
- Field "Description" [\#224](https://github.com/rero/rero-ils/issues/224)
- Overlap of opening hours [\#222](https://github.com/rero/rero-ils/issues/222)
- Date exceptions : repeat [\#155](https://github.com/rero/rero-ils/issues/155)
- Header not auto-hide sticky for circulation pages [\#144](https://github.com/rero/rero-ils/issues/144)
- Action delete on record [\#142](https://github.com/rero/rero-ils/issues/142)

**Closed issues:**

- Request on an item which is checked out [\#235](https://github.com/rero/rero-ils/issues/235)
- Socket closed in worker [\#82](https://github.com/rero/rero-ils/issues/82)
- Missing message to the librarian when a requested item is checked in [\#58](https://github.com/rero/rero-ils/issues/58)
- Wrong circulation status after checkin [\#51](https://github.com/rero/rero-ils/issues/51)
- A request should block the renewal [\#38](https://github.com/rero/rero-ils/issues/38)

**Merged pull requests:**

- US717 and 778 [\#313](https://github.com/rero/rero-ils/pull/313) ([jma](https://github.com/jma))
- config: Sentry support [\#310](https://github.com/rero/rero-ils/pull/310) ([jma](https://github.com/jma))
- US737: Two organisations for the minimal consortial model [\#308](https://github.com/rero/rero-ils/pull/308) ([jma](https://github.com/jma))
- tasks: celery version constraint addition [\#307](https://github.com/rero/rero-ils/pull/307) ([jma](https://github.com/jma))
- global: test coverage and docs for non modules [\#294](https://github.com/rero/rero-ils/pull/294) ([BadrAly](https://github.com/BadrAly))
- global: test coverage and docs for documents [\#293](https://github.com/rero/rero-ils/pull/293) ([BadrAly](https://github.com/BadrAly))
- global: test coverage and docs for loans [\#292](https://github.com/rero/rero-ils/pull/292) ([BadrAly](https://github.com/BadrAly))
- global: test coverage and docs for patrons [\#290](https://github.com/rero/rero-ils/pull/290) ([BadrAly](https://github.com/BadrAly))
- global: test coverage and docs for items [\#289](https://github.com/rero/rero-ils/pull/289) ([BadrAly](https://github.com/BadrAly))
- global: test coverage and docs for libraries [\#288](https://github.com/rero/rero-ils/pull/288) ([BadrAly](https://github.com/BadrAly))
- consortium: metada for two organisations [\#287](https://github.com/rero/rero-ils/pull/287) ([jma](https://github.com/jma))
- global: test coverage and docs for organisations [\#283](https://github.com/rero/rero-ils/pull/283) ([BadrAly](https://github.com/BadrAly))
- global: test coverage and docs for locations [\#282](https://github.com/rero/rero-ils/pull/282) ([BadrAly](https://github.com/BadrAly))
- circulation: correct item status after checkin a requested item [\#281](https://github.com/rero/rero-ils/pull/281) ([BadrAly](https://github.com/BadrAly))
- user interface: patron type name and library name [\#280](https://github.com/rero/rero-ils/pull/280) ([jma](https://github.com/jma))
- global: test coverage and docs for patron types [\#279](https://github.com/rero/rero-ils/pull/279) ([BadrAly](https://github.com/BadrAly))
- user interface: pickup library instead of pickup location [\#278](https://github.com/rero/rero-ils/pull/278) ([jma](https://github.com/jma))
- global: test coverage and docs for item types [\#277](https://github.com/rero/rero-ils/pull/277) ([BadrAly](https://github.com/BadrAly))
- global: test coverage and docs for cipo [\#276](https://github.com/rero/rero-ils/pull/276) ([BadrAly](https://github.com/BadrAly))
- circulation: patron request blocks item renewals [\#274](https://github.com/rero/rero-ils/pull/274) ([BadrAly](https://github.com/BadrAly))
- fix: a fix for loan extension assert problem [\#272](https://github.com/rero/rero-ils/pull/272) ([BadrAly](https://github.com/BadrAly))
- Delete add item button in the document search view [\#268](https://github.com/rero/rero-ils/pull/268) ([Garfield-fr](https://github.com/Garfield-fr))
- circulation: possibility to check-out in-transit items [\#267](https://github.com/rero/rero-ils/pull/267) ([BadrAly](https://github.com/BadrAly))
- circulation: renewal due date from current\_date [\#265](https://github.com/rero/rero-ils/pull/265) ([BadrAly](https://github.com/BadrAly))
- ui: library exception button [\#261](https://github.com/rero/rero-ils/pull/261) ([Garfield-fr](https://github.com/Garfield-fr))
- ui: notification [\#258](https://github.com/rero/rero-ils/pull/258) ([Garfield-fr](https://github.com/Garfield-fr))
- library exceptions date: improvement [\#257](https://github.com/rero/rero-ils/pull/257) ([Garfield-fr](https://github.com/Garfield-fr))
- ALL: invenio 3.1 support [\#255](https://github.com/rero/rero-ils/pull/255) ([jma](https://github.com/jma))
- admin: field description not mandatory [\#253](https://github.com/rero/rero-ils/pull/253) ([Garfield-fr](https://github.com/Garfield-fr))
- library admin: improvement [\#251](https://github.com/rero/rero-ils/pull/251) ([Garfield-fr](https://github.com/Garfield-fr))

## [v0.1.0a21](https://github.com/rero/rero-ils/tree/v0.1.0a21) (2019-03-28)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a20...v0.1.0a21)

**Implemented enhancements:**

- Redirect to document detailed view after document or item edition. [\#226](https://github.com/rero/rero-ils/issues/226)
- Identify the two separate displays in the person detailed view [\#137](https://github.com/rero/rero-ils/issues/137)
- Pager not to display if only 1 page of results [\#123](https://github.com/rero/rero-ils/issues/123)
- pytest Elasticsearch [\#114](https://github.com/rero/rero-ils/issues/114)
- Years facet behaviour [\#92](https://github.com/rero/rero-ils/issues/92)
- Status "Not available" when item is missing [\#47](https://github.com/rero/rero-ils/issues/47)
- No button to return to the view we come from \(like "Back to the results" for example\) [\#36](https://github.com/rero/rero-ils/issues/36)
- Items with active transactions can be deleted without any warning [\#34](https://github.com/rero/rero-ils/issues/34)
- Record deletion without checking the attached records [\#12](https://github.com/rero/rero-ils/issues/12)

**Closed issues:**

- Link from item view to patron check-in/check-out broken [\#234](https://github.com/rero/rero-ils/issues/234)
- Circulation UI: "an error occurs on the server: \[object Object\]" [\#233](https://github.com/rero/rero-ils/issues/233)
- No check when deleting ptty and itty, resulting in broken cipo. [\#227](https://github.com/rero/rero-ils/issues/227)
- Creation of a library: fields already completed [\#221](https://github.com/rero/rero-ils/issues/221)
- Admin resources menu : harmonize editor headings texts [\#215](https://github.com/rero/rero-ils/issues/215)
- Request menu don't display the pickup\_name field [\#170](https://github.com/rero/rero-ils/issues/170)
- After signing up, all pages respond with an internal server error. [\#164](https://github.com/rero/rero-ils/issues/164)
- Date exception: not translated [\#163](https://github.com/rero/rero-ils/issues/163)
- Saved item type [\#143](https://github.com/rero/rero-ils/issues/143)
- brief view for logged user not reliable [\#129](https://github.com/rero/rero-ils/issues/129)
- Item and Patron fixtures to reflect the new item/patron types [\#126](https://github.com/rero/rero-ils/issues/126)
- Layouts issues and remarks [\#121](https://github.com/rero/rero-ils/issues/121)
- Covers not displaying [\#120](https://github.com/rero/rero-ils/issues/120)
- Person search brief view: some information missing [\#118](https://github.com/rero/rero-ils/issues/118)
- Result list, page browse [\#117](https://github.com/rero/rero-ils/issues/117)
- Simple search does not return some results [\#93](https://github.com/rero/rero-ils/issues/93)
- A new search should remove all filters [\#88](https://github.com/rero/rero-ils/issues/88)
- deduplication of uri [\#84](https://github.com/rero/rero-ils/issues/84)
- Edit buttons \(translations\) [\#76](https://github.com/rero/rero-ils/issues/76)
- location validation for items [\#70](https://github.com/rero/rero-ils/issues/70)
- Change the color of the "circulation transaction creation" print confirmation message [\#64](https://github.com/rero/rero-ils/issues/64)
- Missing translation of "requested items" [\#56](https://github.com/rero/rero-ils/issues/56)
- Availabilty information message not translated on the search results page [\#54](https://github.com/rero/rero-ils/issues/54)
- Broken link in circulation table [\#50](https://github.com/rero/rero-ils/issues/50)
- Flash notification for "in transit" at checkin [\#49](https://github.com/rero/rero-ils/issues/49)
- Patron without barcode [\#48](https://github.com/rero/rero-ils/issues/48)
- Default sort of demand list [\#45](https://github.com/rero/rero-ils/issues/45)
- Links to library/member or location detailed view as a patron [\#43](https://github.com/rero/rero-ils/issues/43)
- Confirmation message after record creation [\#40](https://github.com/rero/rero-ils/issues/40)
- Scope of search bar not always visible [\#39](https://github.com/rero/rero-ils/issues/39)
- Search by patron\_full\_name does not check the role "patrons"  [\#29](https://github.com/rero/rero-ils/issues/29)
- renewal counts [\#28](https://github.com/rero/rero-ils/issues/28)
- Lost password workflow only in English [\#3](https://github.com/rero/rero-ils/issues/3)

**Merged pull requests:**

- API: subject facet resolution [\#250](https://github.com/rero/rero-ils/pull/250) ([jma](https://github.com/jma))
- translations: version v.0.1.0a21 [\#249](https://github.com/rero/rero-ils/pull/249) ([iGormilhit](https://github.com/iGormilhit))
- DEPLOY: autocomplete resolution for deployement [\#248](https://github.com/rero/rero-ils/pull/248) ([jma](https://github.com/jma))
- TRANSLATIONS: translations command line resolution [\#247](https://github.com/rero/rero-ils/pull/247) ([jma](https://github.com/jma))
- UI: editor previous page redirection [\#246](https://github.com/rero/rero-ils/pull/246) ([jma](https://github.com/jma))
- UI: clear library form after edit [\#245](https://github.com/rero/rero-ils/pull/245) ([jma](https://github.com/jma))
- UI: links to authorities in the document editor [\#244](https://github.com/rero/rero-ils/pull/244) ([jma](https://github.com/jma))
- Circulation UI: Checkout possible according to circ policy [\#243](https://github.com/rero/rero-ils/pull/243) ([BadrAly](https://github.com/BadrAly))
- CIRCULATION: link from item details to circ UI [\#241](https://github.com/rero/rero-ils/pull/241) ([BadrAly](https://github.com/BadrAly))
- user interface: front page and header [\#240](https://github.com/rero/rero-ils/pull/240) ([iGormilhit](https://github.com/iGormilhit))
- RECORDS: can\_delete fix for item and patron types [\#239](https://github.com/rero/rero-ils/pull/239) ([BadrAly](https://github.com/BadrAly))
- ES: person language mapping [\#238](https://github.com/rero/rero-ils/pull/238) ([rerowep](https://github.com/rerowep))
- UI: persons and documents public search view [\#236](https://github.com/rero/rero-ils/pull/236) ([jma](https://github.com/jma))
- user interface: menus structure [\#228](https://github.com/rero/rero-ils/pull/228) ([iGormilhit](https://github.com/iGormilhit))
- ES: loan mapping [\#220](https://github.com/rero/rero-ils/pull/220) ([rerowep](https://github.com/rerowep))
- Circulation: Policy adapting for CIRC UI [\#219](https://github.com/rero/rero-ils/pull/219) ([BadrAly](https://github.com/BadrAly))
- Circulation: nested mapping for cipo settings [\#218](https://github.com/rero/rero-ils/pull/218) ([BadrAly](https://github.com/BadrAly))
- UI: typeahead support for document search [\#216](https://github.com/rero/rero-ils/pull/216) ([jma](https://github.com/jma))
- Circulation Policies: Locate policy using item/patorn types pair [\#214](https://github.com/rero/rero-ils/pull/214) ([BadrAly](https://github.com/BadrAly))
- SERIALIZER: Fix resolve [\#212](https://github.com/rero/rero-ils/pull/212) ([Garfield-fr](https://github.com/Garfield-fr))
- user interface: translations [\#211](https://github.com/rero/rero-ils/pull/211) ([iGormilhit](https://github.com/iGormilhit))
- Circulation: Circ policies backend [\#210](https://github.com/rero/rero-ils/pull/210) ([Garfield-fr](https://github.com/Garfield-fr))
- admin UI: fix and translations [\#208](https://github.com/rero/rero-ils/pull/208) ([iGormilhit](https://github.com/iGormilhit))
- repository: commit template [\#207](https://github.com/rero/rero-ils/pull/207) ([iGormilhit](https://github.com/iGormilhit))
- all: several fixes [\#206](https://github.com/rero/rero-ils/pull/206) ([jma](https://github.com/jma))
- DATA: $ref for mef persons [\#205](https://github.com/rero/rero-ils/pull/205) ([rerowep](https://github.com/rerowep))
- Circulation: Circ policies backend [\#204](https://github.com/rero/rero-ils/pull/204) ([BadrAly](https://github.com/BadrAly))
- ADMIN UI: URL parameters and facets [\#202](https://github.com/rero/rero-ils/pull/202) ([jma](https://github.com/jma))
- Admin: Modal dialog [\#201](https://github.com/rero/rero-ils/pull/201) ([Garfield-fr](https://github.com/Garfield-fr))
- User interface: admin pages and jinja templates [\#200](https://github.com/rero/rero-ils/pull/200) ([jma](https://github.com/jma))
- DEPLOYMENT: docker [\#198](https://github.com/rero/rero-ils/pull/198) ([rerowep](https://github.com/rerowep))
- Patron: Add communication channel [\#197](https://github.com/rero/rero-ils/pull/197) ([Garfield-fr](https://github.com/Garfield-fr))
- RECORDS: can\_delete [\#195](https://github.com/rero/rero-ils/pull/195) ([BadrAly](https://github.com/BadrAly))
- Angular lint [\#194](https://github.com/rero/rero-ils/pull/194) ([Garfield-fr](https://github.com/Garfield-fr))
- API: resolvers [\#192](https://github.com/rero/rero-ils/pull/192) ([rerowep](https://github.com/rerowep))
- Admin: Circulation policy [\#191](https://github.com/rero/rero-ils/pull/191) ([Garfield-fr](https://github.com/Garfield-fr))
- ALL: $ref as link mecanism [\#188](https://github.com/rero/rero-ils/pull/188) ([jma](https://github.com/jma))
- Layout: refactoring [\#186](https://github.com/rero/rero-ils/pull/186) ([iGormilhit](https://github.com/iGormilhit))
- Scripts: MEF harvesting [\#185](https://github.com/rero/rero-ils/pull/185) ([BadrAly](https://github.com/BadrAly))
- Circulation policies settings [\#171](https://github.com/rero/rero-ils/pull/171) ([BadrAly](https://github.com/BadrAly))
- User: critical bug at menu initialization [\#165](https://github.com/rero/rero-ils/pull/165) ([iGormilhit](https://github.com/iGormilhit))
- ADMIN: Switch translation on the fly [\#162](https://github.com/rero/rero-ils/pull/162) ([Garfield-fr](https://github.com/Garfield-fr))
- Admin interface: checkin/checkout implementation [\#161](https://github.com/rero/rero-ils/pull/161) ([jma](https://github.com/jma))
- Library translation [\#160](https://github.com/rero/rero-ils/pull/160) ([Garfield-fr](https://github.com/Garfield-fr))
- Basic circulation policies [\#158](https://github.com/rero/rero-ils/pull/158) ([BadrAly](https://github.com/BadrAly))
- FIXTURE: libraries opening hours and exception dates [\#157](https://github.com/rero/rero-ils/pull/157) ([NicolasLabat](https://github.com/NicolasLabat))
- Library creation [\#156](https://github.com/rero/rero-ils/pull/156) ([Garfield-fr](https://github.com/Garfield-fr))
- Maj circulation ui \#724 [\#153](https://github.com/rero/rero-ils/pull/153) ([jma](https://github.com/jma))
- Libraries: Form Validation [\#152](https://github.com/rero/rero-ils/pull/152) ([Garfield-fr](https://github.com/Garfield-fr))
- Library: date exceptions [\#151](https://github.com/rero/rero-ils/pull/151) ([rerowep](https://github.com/rerowep))
- Admin interface: menu refactoring [\#150](https://github.com/rero/rero-ils/pull/150) ([iGormilhit](https://github.com/iGormilhit))
- replace function [\#149](https://github.com/rero/rero-ils/pull/149) ([rerowep](https://github.com/rerowep))
- Circulation: configuration [\#148](https://github.com/rero/rero-ils/pull/148) ([iGormilhit](https://github.com/iGormilhit))
- Libraries: add options opening\_hours + new library editor [\#147](https://github.com/rero/rero-ils/pull/147) ([Garfield-fr](https://github.com/Garfield-fr))
- Circulation: invenio-circulation integration [\#146](https://github.com/rero/rero-ils/pull/146) ([BadrAly](https://github.com/BadrAly))
- Issue: Identify the two separate displays in the person detailed view [\#141](https://github.com/rero/rero-ils/pull/141) ([Garfield-fr](https://github.com/Garfield-fr))
- ISSUSES: patron parcode [\#140](https://github.com/rero/rero-ils/pull/140) ([rerowep](https://github.com/rerowep))
- User interface: menu list [\#139](https://github.com/rero/rero-ils/pull/139) ([rerowep](https://github.com/rerowep))
- admin ui: angular skeleton [\#138](https://github.com/rero/rero-ils/pull/138) ([jma](https://github.com/jma))
- Circulation: integration of invenio-circulation APIs [\#136](https://github.com/rero/rero-ils/pull/136) ([BadrAly](https://github.com/BadrAly))
- Package: requests upgrade [\#135](https://github.com/rero/rero-ils/pull/135) ([BadrAly](https://github.com/BadrAly))

## [v0.1.0a20](https://github.com/rero/rero-ils/tree/v0.1.0a20) (2018-10-31)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a19...v0.1.0a20)

**Implemented enhancements:**

- Circulation policy: Display the unit "days"  units  [\#127](https://github.com/rero/rero-ils/issues/127)

**Closed issues:**

- Circulation policy form allows negative values [\#125](https://github.com/rero/rero-ils/issues/125)
- api harvester size [\#111](https://github.com/rero/rero-ils/issues/111)
- CSV export not working [\#103](https://github.com/rero/rero-ils/issues/103)

**Merged pull requests:**

- User interface: header menu [\#134](https://github.com/rero/rero-ils/pull/134) ([iGormilhit](https://github.com/iGormilhit))
- circulation ui: member to library [\#133](https://github.com/rero/rero-ils/pull/133) ([iGormilhit](https://github.com/iGormilhit))
- Member to library [\#132](https://github.com/rero/rero-ils/pull/132) ([rerowep](https://github.com/rerowep))
- frontend: translations [\#130](https://github.com/rero/rero-ils/pull/130) ([iGormilhit](https://github.com/iGormilhit))
- Circulation policy: issues [\#128](https://github.com/rero/rero-ils/pull/128) ([BadrAly](https://github.com/BadrAly))
-  Circulation: Policy configuration [\#124](https://github.com/rero/rero-ils/pull/124) ([BadrAly](https://github.com/BadrAly))
- frontend: cleaning [\#122](https://github.com/rero/rero-ils/pull/122) ([iGormilhit](https://github.com/iGormilhit))
- Item Types: Add resource [\#116](https://github.com/rero/rero-ils/pull/116) ([Garfield-fr](https://github.com/Garfield-fr))
- Patron Types: Add resource [\#115](https://github.com/rero/rero-ils/pull/115) ([Garfield-fr](https://github.com/Garfield-fr))
- apiharvester: fix size [\#113](https://github.com/rero/rero-ils/pull/113) ([rerowep](https://github.com/rerowep))
- frontend: refactoring [\#110](https://github.com/rero/rero-ils/pull/110) ([Garfield-fr](https://github.com/Garfield-fr))
- frontend: refactor layout [\#107](https://github.com/rero/rero-ils/pull/107) ([jma](https://github.com/jma))

## [v0.1.0a19](https://github.com/rero/rero-ils/tree/v0.1.0a19) (2018-10-11)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a18...v0.1.0a19)

**Implemented enhancements:**

- Item status isn't automatically updated in the item brief view [\#20](https://github.com/rero/rero-ils/issues/20)

**Closed issues:**

- Jinja error after creating a document without identifiers \(ISBN\) [\#109](https://github.com/rero/rero-ils/issues/109)
- Angularjs: Remove invenioSearchConfig \(thumbnail.js\) [\#94](https://github.com/rero/rero-ils/issues/94)
- Too many `electronic\_location` values for ebooks [\#71](https://github.com/rero/rero-ils/issues/71)
- User roles display [\#53](https://github.com/rero/rero-ils/issues/53)
- Uppercase in the facets [\#44](https://github.com/rero/rero-ils/issues/44)

**Merged pull requests:**

- can delete [\#105](https://github.com/rero/rero-ils/pull/105) ([rerowep](https://github.com/rerowep))
- missing format\_date\_filter in items/view [\#104](https://github.com/rero/rero-ils/pull/104) ([rerowep](https://github.com/rerowep))
- git: gitignore extension [\#102](https://github.com/rero/rero-ils/pull/102) ([iGormilhit](https://github.com/iGormilhit))
- oaiharvest port 8443 [\#100](https://github.com/rero/rero-ils/pull/100) ([rerowep](https://github.com/rerowep))
- feat: Remove invenioSearchConfig and replace with invenioConfig [\#99](https://github.com/rero/rero-ils/pull/99) ([Garfield-fr](https://github.com/Garfield-fr))
- fixtures: users following personas templates [\#98](https://github.com/rero/rero-ils/pull/98) ([iGormilhit](https://github.com/iGormilhit))
- identifier for person link [\#97](https://github.com/rero/rero-ils/pull/97) ([rerowep](https://github.com/rerowep))
- feat: add source facet and source badge on briew view person [\#96](https://github.com/rero/rero-ils/pull/96) ([Garfield-fr](https://github.com/Garfield-fr))
- Person: Brief view [\#95](https://github.com/rero/rero-ils/pull/95) ([Garfield-fr](https://github.com/Garfield-fr))
- person detailed view [\#90](https://github.com/rero/rero-ils/pull/90) ([rerowep](https://github.com/rerowep))
- harvest mef [\#85](https://github.com/rero/rero-ils/pull/85) ([rerowep](https://github.com/rerowep))
- facets [\#78](https://github.com/rero/rero-ils/pull/78) ([rerowep](https://github.com/rerowep))
- fix: add exception on pipenv check [\#77](https://github.com/rero/rero-ils/pull/77) ([Garfield-fr](https://github.com/Garfield-fr))
- feat: add cover render services to brief and full view [\#75](https://github.com/rero/rero-ils/pull/75) ([jma](https://github.com/jma))
- documentation: installation and contributing [\#74](https://github.com/rero/rero-ils/pull/74) ([iGormilhit](https://github.com/iGormilhit))
- fix: link on assets with invenio collect [\#73](https://github.com/rero/rero-ils/pull/73) ([jma](https://github.com/jma))
- App data merge [\#72](https://github.com/rero/rero-ils/pull/72) ([jma](https://github.com/jma))

## [v0.1.0a18](https://github.com/rero/rero-ils/tree/v0.1.0a18) (2018-08-23)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a17...v0.1.0a18)

**Merged pull requests:**

- feat: ebooks harvesting [\#69](https://github.com/rero/rero-ils/pull/69) ([jma](https://github.com/jma))
- search: AND by default [\#68](https://github.com/rero/rero-ils/pull/68) ([jma](https://github.com/jma))

## [v0.1.0a17](https://github.com/rero/rero-ils/tree/v0.1.0a17) (2018-08-20)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a16...v0.1.0a17)

**Closed issues:**

- Due date format should not display hours, minutes and seconds [\#66](https://github.com/rero/rero-ils/issues/66)
- Creation of item fails because of misspelled key label in the form options file [\#61](https://github.com/rero/rero-ils/issues/61)
- Translation of general status of documents [\#60](https://github.com/rero/rero-ils/issues/60)
- Barcode not displayed on the request tab of the circulation UI [\#59](https://github.com/rero/rero-ils/issues/59)
- The patron profile is displaying the loan start date instead of the loan due date [\#57](https://github.com/rero/rero-ils/issues/57)
- Display item status on item detailed view [\#46](https://github.com/rero/rero-ils/issues/46)
- Internal server error when adding a new item [\#42](https://github.com/rero/rero-ils/issues/42)
- Error not specified at patron creation [\#9](https://github.com/rero/rero-ils/issues/9)

**Merged pull requests:**

- feat: new shuffled export [\#67](https://github.com/rero/rero-ils/pull/67) ([rerowep](https://github.com/rerowep))
- feat: add icons by doc type [\#65](https://github.com/rero/rero-ils/pull/65) ([BadrAly](https://github.com/BadrAly))
- add new document types [\#63](https://github.com/rero/rero-ils/pull/63) ([rerowep](https://github.com/rerowep))

## [v0.1.0a16](https://github.com/rero/rero-ils/tree/v0.1.0a16) (2018-07-04)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a15...v0.1.0a16)

**Implemented enhancements:**

- A confirmation message should be displayed after the "Delete" action \(item or bib record for example\) [\#35](https://github.com/rero/rero-ils/issues/35)

**Closed issues:**

- Translation of languages item selection no coherent [\#33](https://github.com/rero/rero-ils/issues/33)

## [v0.1.0a15](https://github.com/rero/rero-ils/tree/v0.1.0a15) (2018-06-26)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a14...v0.1.0a15)

## [v0.1.0a14](https://github.com/rero/rero-ils/tree/v0.1.0a14) (2018-06-26)

[Full Changelog](https://github.com/rero/rero-ils/compare/v0.1.0a13...v0.1.0a14)

**Implemented enhancements:**

- No Cancel button in record edition view [\#11](https://github.com/rero/rero-ils/issues/11)

**Closed issues:**

- Prettyfy the export JSON output. [\#32](https://github.com/rero/rero-ils/issues/32)
- Typo on the homepage in French [\#31](https://github.com/rero/rero-ils/issues/31)
- Not possible to save patrons after removing the phone number [\#27](https://github.com/rero/rero-ils/issues/27)
- Error when trying to edit items [\#26](https://github.com/rero/rero-ils/issues/26)
- Item barcode uniqueness not recognised [\#19](https://github.com/rero/rero-ils/issues/19)



\* *This Changelog was automatically generated by [github_changelog_generator](https://github.com/github-changelog-generator/github-changelog-generator)*
