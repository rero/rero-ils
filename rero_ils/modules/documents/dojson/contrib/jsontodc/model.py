# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""RERO-ILS to Dublin Core conversion model definition.

This module implements DoJSON transformation rules for converting RERO ILS internal JSON document format to Dublin
Core (DC) metadata format. Dublin Core is a simple and widely-used metadata standard with 15 core elements.

The transformation provides mappings from RERO ILS complex bibliographic structures to simplified Dublin Core elements:

    - dc:title: Main title with responsibility statement
    - dc:creator: Primary creators (authors, composers, photographers)
    - dc:contributor: Other contributors
    - dc:description: Summaries, notes, dissertation info
    - dc:language: Language codes (ISO 639)
    - dc:publisher: Publishers and publication dates
    - dc:type: Document type and subtype
    - dc:identifier: ISBN, ISSN, local identifiers
    - dc:relation: Related works and editions
    - dc:subject: Subject headings and keywords

Key Classes:
    DublinCoreOverdo: Specialized DoJSON Overdo for Dublin Core conversion

Key Features:
    - Language-aware entity resolution for multilingual metadata
    - Role-based separation of creators vs contributors (using CREATOR_ROLES from serializers.base)
    - Automatic title formatting with responsibility statements
    - Multiple identifier format handling
    - Entity type-aware subject processing

See Also:
    - Dublin Core Metadata Initiative: https://dublincore.org/
    - Dublin Core Terms: https://www.dublincore.org/specifications/dublin-core/dcmi-terms/
    - DoJSON: https://dojson.readthedocs.io/
"""

from dojson import Overdo, utils
from flask_babel import gettext as _

from rero_ils.modules.documents.extensions import TitleExtension
from rero_ils.modules.documents.serializers.base import CREATOR_ROLES
from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.entities.remote_entities.utils import get_entity_localized_value


class DublinCoreOverdo(Overdo):
    """DoJSON Overdo extension for RERO ILS to Dublin Core transformation.

    This class extends DoJSON's Overdo to convert RERO ILS bibliographic records
    to Dublin Core format. It implements simplified mapping rules that reduce
    complex RERO ILS structures to the 15 core Dublin Core elements.

    The transformation process:

    1. Sets target language for multilingual field resolution
    2. Applies DoJSON transformation rules for each DC element
    3. Post-processes title field with formatted text
    4. Adds local identifier (PID) to identifiers list

    Dublin Core elements generated:

    - titles: Formatted main title with subtitle and responsibility
    - creators: Primary creators based on role codes
    - contributors: Other contributors
    - descriptions: Summaries, notes, dissertation info
    - languages: ISO 639 language codes
    - publishers: Publisher names from statements
    - dates: Publication dates (start-end)
    - types: Translated document types
    - identifiers: ISBNs, ISSNs, local IDs
    - relations: Related works
    - subjects: Subject headings

    :ivar language: Target language for entity resolution and translations.
    :vartype language: str

    .. note::

        Unlike MARC 21 conversion, Dublin Core output is intentionally simplified
        and may lose some bibliographic detail present in the source record.

    .. seealso::

        DoJSON Overdo: https://dojson.readthedocs.io/en/latest/api.html#overdo
    """

    def do(self, blob, ignore_missing=True, exception_handlers=None, language="fr"):
        """Transform RERO ILS JSON document to Dublin Core format.

        This method orchestrates the complete transformation from RERO ILS
        internal format to Dublin Core. It applies transformation rules,
        post-processes the title field, and adds the local identifier.

        Transformation pipeline:

        1. Sets language attribute for multilingual field resolution
        2. Executes DoJSON transformation rules for each DC element
        3. Formats title with subtitle and responsibility statement
        4. Prepends local PID to identifiers list

        :param blob: RERO ILS document dictionary to transform containing pid,
            title, contribution, summary, note, dissertation, language,
            provisionActivity, type, identifiedBy, and subjects.
        :type blob: dict
        :param ignore_missing: If False, raises MissingRule when a field has
            no transformation rule. Defaults to True.
        :type ignore_missing: bool, optional
        :param exception_handlers: Custom exception handlers for non-standard
            field processing. Defaults to None.
        :type exception_handlers: dict, optional
        :param language: Target language code for entity resolution and type
            translations. Affects which authorized access point is selected
            for multilingual entities. Defaults to "fr".
        :type language: str, optional
        :returns: Dublin Core representation with titles, creators, contributors,
            descriptions, languages, publishers, dates, types, identifiers,
            relations, and subjects.
        :rtype: dict
        :raises MissingRule: If ignore_missing=False and a field lacks a
            transformation rule.

        .. note::

            - Title formatting combines mainTitle, subtitle, and responsibility
            - Only bf:Title type titles are used for the formatted title
            - PID is always the first identifier in the list

        Example::

            converter = DublinCoreOverdo()
            rero_doc = {
                'pid': 'doc123',
                'title': [{
                    'type': 'bf:Title',
                    'mainTitle': [{'value': 'Sample Title'}],
                    'subtitle': [{'value': 'A Study'}]
                }],
                'responsibilityStatement': [[{'value': 'John Doe'}]],
                'contribution': [...],
                ...
            }
            dc_record = converter.do(rero_doc, language='en')
            dc_record['titles']
            # ['Sample Title : A Study / John Doe']
        """
        self.language = language

        result = super().do(blob, ignore_missing=ignore_missing, exception_handlers=exception_handlers)

        # Post-process title: extract bf:Title entries and format with subtitle
        # and responsibility statement for DC title element
        titles = blob.get("title", [])
        bf_titles = list(filter(lambda t: t.get("type") == "bf:Title", titles))

        if text := TitleExtension.format_text(
            titles=bf_titles,
            responsabilities=blob.get("responsibilityStatement", []),
            with_subtitle=True,
        ):
            result["titles"] = [text]

        # Prepend local PID as first identifier in bf:Local format
        if pid := blob.get("pid"):
            result.setdefault("identifiers", []).insert(0, f"bf:Local|{pid}")
        return result


dublincore = DublinCoreOverdo()


@dublincore.over("creators", "contribution")
@utils.for_each_value
@utils.ignore_value
def json_to_contributors(self, key, value):
    """Extract creators and contributors from contribution entities.

    This function implements role-based separation of creators vs contributors
    in Dublin Core. Contributors with roles in CREATOR_ROLES become dc:creator,
    while others become dc:contributor.

    The function:

    1. Resolves entity authorized access point (language-aware)
    2. Falls back to generic authorized_access_point if needed
    3. Checks if role is in CREATOR_ROLES
    4. If creator role: returns value for dc:creator
    5. If contributor role: appends to contributors list and returns None

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("contribution").
    :type key: str
    :param value: Contribution object containing entity (with authorized_access_point)
        and role (list of MARC relator codes).
    :type value: dict
    :returns: Authorized access point if role is in CREATOR_ROLES, None otherwise
        (contributor added directly to self).
    :rtype: str or None

    .. note::

        - Contributors are written directly to self["contributors"] to avoid
          duplication in the creators list
        - Language-aware resolution uses get_entity_localized_value()
        - Returns None if no authorized access point is found

    Example::

        value = {
            'entity': {'authorized_access_point': 'Doe, John'},
            'role': ['aut']  # Author role
        }
        json_to_contributors(dc_record, 'contribution', value)
        # Returns: 'Doe, John'  # Added to dc:creator

        value['role'] = ['edt']  # Editor role
        json_to_contributors(dc_record, 'contribution', value)
        # Returns: None  # Added to dc:contributor instead
    """
    authorized_access_point = get_entity_localized_value(
        entity=value.get("entity", {}),
        key="authorized_access_point",
        language=dublincore.language,
    )
    result = authorized_access_point
    if result is None:
        result = value.get("entity", {}).get("authorized_access_point")

    if result:
        roles = value.get("role") or []
        if isinstance(roles, str):
            roles = [roles]
        if any(role in CREATOR_ROLES for role in roles):
            return result

        contributors = self.get("contributors", [])
        contributors.append(result)
        # save contributors directly into self
        self["contributors"] = contributors
    return None


@dublincore.over("descriptions", "^(summary|note|dissertation|supplementaryContent)")
@utils.ignore_value
def json_to_descriptions(self, key, value):
    """Aggregate description data from multiple RERO ILS fields into dc:description.

    Consolidates various descriptive fields into a single Dublin Core description
    element. This includes summaries, notes, dissertation information, and
    supplementary content.

    Field mappings:

    - supplementaryContent: Added directly
    - summary: Extracts all label values (multiple languages)
    - note: Extracts label field
    - dissertation: Extracts label field

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key (summary, note, dissertation, supplementaryContent).
    :type key: str
    :param value: Field value(s) to process. Can be string (supplementaryContent),
        dict with label (note or dissertation), or dict with label list (summary).
    :type value: list or dict
    :returns: None. Descriptions are written directly to self["descriptions"].
    :rtype: None

    .. note::

        - Accumulates values from multiple calls (all description sources)
        - Summary labels are flattened (all language variants included)
        - Empty descriptions list is not written to self

    Example::

        # First call with summary
        value = {'label': [{'value': 'A comprehensive study'}]}
        json_to_descriptions(dc, 'summary', value)
        dc['descriptions']
        # => ['A comprehensive study']

        # Second call with note
        value = {'label': 'Bibliography: p. 200-210'}
        json_to_descriptions(dc, 'note', value)
        dc['descriptions']
        # => ['A comprehensive study', 'Bibliography: p. 200-210']
    """
    descriptions = self.get("descriptions", [])
    for data in utils.force_list(value):
        if key == "supplementaryContent":
            descriptions.append(data)
        elif key == "summary":
            descriptions += [v for v in (label.get("value") for label in data.get("label", [])) if v is not None]
        elif label := data.get("label"):
            descriptions.append(label)
    if descriptions:
        # write the descriptions directly into self
        self["descriptions"] = descriptions


@dublincore.over("languages", "^language")
@utils.ignore_value
def json_to_languages(self, key, value):
    """Extract language codes for dc:language element.

    Converts RERO ILS language objects to simple ISO 639 language codes
    for Dublin Core.

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("language").
    :type key: str
    :param value: Language object(s) with value (ISO 639-2/B code) and
        optional type field.
    :type value: list or dict
    :returns: List of ISO 639 language codes, or None if no languages found.
    :rtype: list or None

    Example::

        value = [{'value': 'eng'}, {'value': 'fre'}]
        json_to_languages(dc, 'language', value)
        # Returns: ['eng', 'fre']
    """
    languages = [lang_code for language in utils.force_list(value) if (lang_code := language.get("value"))]
    return languages or None


@dublincore.over("publishers", "^provisionActivity")
@utils.ignore_value
def json_to_dates(self, key, value):
    """Extract publisher names and publication dates from provisionActivity.

    Processes provisionActivity to populate both dc:publisher and dc:date elements.
    Publisher names (dc:publisher) are extracted from all provisionActivity types,
    while publication dates (dc:date) are only extracted for bf:Publication activities.

    Extraction rules:

    - Date (dc:date): Only from bf:Publication, uses startDate and optional
      endDate, format "YYYY" or "YYYY-YYYY", only first publication date used
    - Publisher (dc:publisher): From bf:Agent statements, takes first label
      value, all agents included

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("provisionActivity").
    :type key: str
    :param value: List of provision activity objects with type, startDate,
        endDate, and statement fields.
    :type value: list
    :returns: None. Publishers and dates written directly to self["publishers"]
        and self["dates"].
    :rtype: None

    .. note::

        - Only processes bf:Publication activities for dates
        - Multiple publisher names can be extracted
        - Date range format: "2020-2023"
        - Single date format: "2020"

    Example::

        value = [{
            'type': 'bf:Publication',
            'startDate': '2020',
            'endDate': '2023',
            'statement': [
                {
                    'type': 'bf:Agent',
                    'label': [{'value': 'Publisher Inc.'}]
                },
                {
                    'type': 'bf:Place',
                    'label': [{'value': 'New York'}]
                }
            ]
        }]
        json_to_dates(dc, 'provisionActivity', value)
        dc['dates']
        # => ['2020-2023']
        dc['publishers']
        # => ['Publisher Inc.']
    """
    publishers = self.get("publishers", [])
    dates = self.get("dates", [])
    for data in value:
        # Extract publication date (only from bf:Publication, and only once)
        # If we have startDate and endDate dates = f"{startDate}-{endDate}"
        # If we have no endDate but a startDate dates = f"{startDate}"
        # If we have no startDate but an endDate dates = f"-{endDate}"
        # If we have no startDate and no endDate, we don't add a date
        if data.get("type") == "bf:Publication" and not dates:
            start_date = str(data.get("startDate") or "")
            date = [start_date]
            if end_date := str(data.get("endDate") or ""):
                date.append(end_date)
            if start_date or end_date:
                dates.append("-".join(date))

        # Extract publisher names from bf:Agent type statements
        statements = data.get("statement", [])
        for statement in statements:
            if statement.get("type") == "bf:Agent":
                # Take first label value (publisher name) from agent statement
                labels = statement.get("label", [])
                if labels and (pub_name := labels[0].get("value")):
                    publishers.append(pub_name)
    # Write accumulated values to DC record
    if dates:
        self["dates"] = dates
    if publishers:
        self["publishers"] = publishers


@dublincore.over("types", "^type")
@utils.for_each_value
@utils.ignore_value
def json_to_types(self, key, value):
    """Convert document types to translated dc:type values.

    Transforms RERO ILS document type information into human-readable,
    translated type strings for Dublin Core. Combines main_type and
    optional subtype with translation.

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("type").
    :type key: str
    :param value: Type object containing main_type and optional subtype codes.
    :type value: dict
    :returns: Translated type string. Format "Main Type / Subtype" with subtype
        or "Main Type" without.
    :rtype: str

    .. note::

        - Uses Flask-Babel gettext (_) for translation
        - Translation uses the language set in dublincore.language
        - Type codes are defined in RERO ILS document type vocabulary

    Example::

        value = {'main_type': 'docmaintype_book', 'subtype': 'docsubtype_e-book'}
        json_to_types(dc, 'type', value)  # Language: en
        # Returns: 'Book / E-book'

        value = {'main_type': 'docmaintype_serial'}
        json_to_types(dc, 'type', value)  # Language: fr
        # Returns: 'Périodique'
    """
    main_type = value.get("main_type")
    if subtype_type := value.get("subtype"):
        return " / ".join([_(main_type), _(subtype_type)])
    return _(main_type)


@dublincore.over("identifiers", "^identifiedBy")
@utils.for_each_value
@utils.ignore_value
def json_to_identifiers(self, key, value):
    """Convert various identifier types to dc:identifier format.

    Transforms RERO ILS identifier objects into formatted strings for Dublin Core.
    Supports multiple identifier types (ISBN, ISSN, DOI, etc.) with optional
    source information.

    Output format:

    - With source: "Type|Value(Source)" (e.g., "bf:Doi|10.1000/xyz(CrossRef)")
    - Without source: "Type|Value" (e.g., "bf:Isbn|9781234567890")

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("identifiedBy").
    :type key: str
    :param value: Identifier object containing type, value, optional source,
        and optional status.
    :type value: dict
    :returns: Formatted identifier string.
    :rtype: str

    .. note::

        - Type prefix uses BIBFRAME vocabulary (bf:Isbn, bf:Issn, etc.)
        - Source is included in parentheses when present
        - Invalid/cancelled identifiers are still included
        - Local PID is prepended separately in do() method

    Example::

        value = {'type': 'bf:Isbn', 'value': '9781234567890'}
        json_to_identifiers(dc, 'identifiedBy', value)
        # Returns: 'bf:Isbn|9781234567890'

        value = {
            'type': 'bf:Doi',
            'value': '10.1000/xyz',
            'source': 'CrossRef'
        }
        json_to_identifiers(dc, 'identifiedBy', value)
        # Returns: 'bf:Doi|10.1000/xyz(CrossRef)'
    """
    itype = value.get("type")
    identifier_value = value.get("value")
    if not itype or not identifier_value:
        return None
    if source := value.get("source"):
        return f"{itype}|{identifier_value}({source})"
    return f"{itype}|{identifier_value}"


@dublincore.over(
    "relations",
    "^(issuedWith|otherEdition|otherPhysicalFormat|precededBy|relatedTo|succeededBy|supplement|supplementTo)",
)
@utils.for_each_value
@utils.ignore_value
def json_to_relations(self, key, value):
    """Extract related work information for dc:relation element.

    Consolidates various relationship fields into dc:relation. Supports both
    labeled relationships (with explicit label) and title-based relationships
    (with title array).

    Relationship types processed:

    - issuedWith: Resources issued together
    - otherEdition: Other editions of the same work
    - otherPhysicalFormat: Same content in different format
    - precededBy: Previous/earlier work
    - relatedTo: Generally related works
    - succeededBy: Subsequent/later work
    - supplement: Supplementary material
    - supplementTo: Work this is a supplement to

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key (relationship type).
    :type key: str
    :param value: Relationship object containing label or title array with
        _text field.
    :type value: dict
    :returns: Relationship description string, or None if neither label nor
        titles are present.
    :rtype: str or None

    .. note::

        - Prefers label over title if both present
        - Multiple titles are joined with ", "
        - Relationship type is not included in output (lost in consolidation)

    Example::

        value = {'label': 'Earlier edition: 1st ed., 2010'}
        json_to_relations(dc, 'precededBy', value)
        # Returns: 'Earlier edition: 1st ed., 2010'

        value = {'title': [{'_text': 'Original French'}, {'_text': 'German trans.'}]}
        json_to_relations(dc, 'otherEdition', value)
        # Returns: 'Original French, German trans.'
    """
    if label := value.get("label"):
        return label
    if titles := [t for title in value.get("title", []) if (t := title.get("_text"))]:
        return ", ".join(titles)
    return None


@dublincore.over("subjects", "^subjects")
@utils.for_each_value
@utils.ignore_value
def json_to_subject(self, key, value):
    """Convert subject entities to dc:subject strings.

    Transforms various entity types into subject heading strings for Dublin Core.
    Handles different entity types with type-specific formatting and language-aware
    resolution for authorized access points.

    Entity type handling:

    - PERSON: Uses language-specific authorized_access_point or preferred_name
    - ORGANISATION: Uses language-specific authorized_access_point or preferred_name
    - PLACE: Uses language-specific authorized_access_point or preferred_name
    - WORK: Combines creator and title with ". - " separator
    - TOPIC: Uses term field
    - TEMPORAL: Uses term field

    :param self: The Dublin Core record being built.
    :type self: dict
    :param key: Source field key ("subjects").
    :type key: str
    :param value: Subject entity object containing type, authorized_access_point,
        preferred_name, creator, title, or term depending on entity type.
    :type value: dict
    :returns: Subject heading string, or None if no suitable value found.
    :rtype: str or None

    .. note::

        - Uses get_entity_localized_value() for language-aware resolution
        - WORK subjects include creator if available
        - Empty results return None instead of empty string

    Example::

        # Person subject
        value = {
            'type': 'bf:Person',
            'authorized_access_point': 'Shakespeare, William, 1564-1616'
        }
        json_to_subject(dc, 'subjects', value)
        # Returns: 'Shakespeare, William, 1564-1616'

        # Work subject
        value = {
            'type': 'bf:Work',
            'creator': 'Homer',
            'title': 'Odyssey'
        }
        json_to_subject(dc, 'subjects', value)
        # Returns: 'Homer. - Odyssey'

        # Topic subject
        value = {'type': 'bf:Topic', 'term': 'Artificial intelligence'}
        json_to_subject(dc, 'subjects', value)
        # Returns: 'Artificial intelligence'
    """
    result = ""
    _type = value.get("type")

    # Person, organisation, or place subjects: use authorized access point
    if _type in [EntityType.PERSON, EntityType.ORGANISATION, EntityType.PLACE]:
        if authorized_access_point := get_entity_localized_value(
            entity=value,
            key="authorized_access_point",
            language=dublincore.language,
        ):
            result = authorized_access_point
        else:
            result = value.get("preferred_name")

    # Work subjects: combine creator and title
    elif _type == EntityType.WORK:
        work = []
        if creator := value.get("creator"):
            work.append(creator)
        if title := value.get("title"):
            work.append(title)
        result = ". - ".join(work)

    # Topic or temporal subjects: use term
    elif _type in [EntityType.TOPIC, EntityType.TEMPORAL]:
        result = value.get("term")

    return result or None
