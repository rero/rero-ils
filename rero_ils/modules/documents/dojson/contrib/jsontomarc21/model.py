# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2024 RERO
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

"""RERO-ILS to MARC 21 conversion model definition.

This module implements DoJSON transformation rules for converting RERO ILS
internal JSON document format to MARC 21 XML format. It provides:

    - Complete field-by-field mapping from RERO ILS JSON to MARC 21
    - Dynamic leader generation based on document type
    - Entity resolution for contributions (authors, contributors)
    - Holdings and items serialization (field 949)
    - Language-aware source ordering for authorized access points
    - Support for filtering by organisation, library, and location

The transformation process:
    1. Generates MARC leader based on document type (position 06-07)
    2. Creates fixed-length data elements (field 008)
    3. Maps bibliographic fields (020-9XX)
    4. Resolves entity references for contributions and subjects
    5. Optionally includes holdings/items data

Key Classes:
    ToMarc21Overdo: Specialized DoJSON Overdo class for MARC 21 conversion

Key Functions:
    do_contribution: Processes contribution entities with language preferences
    do_concept: Processes subject/concept entities
    get_holdings_items: Retrieves holdings and items for a document
    generate_leader: Creates MARC leader based on document characteristics

See Also:
    - MARC 21 Format: https://www.loc.gov/marc/bibliographic/
    - DoJSON: https://dojson.readthedocs.io/
"""

from dojson import utils
from dojson.contrib.to_marc21.model import Underdo
from flask import current_app
from flask_babel import gettext as translate

from rero_ils.dojson.utils import error_print
from rero_ils.modules.documents.models import DocumentFictionType
from rero_ils.modules.documents.utils import display_alternate_graphic_first
from rero_ils.modules.documents.views import create_title_responsibilites
from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.entities.remote_entities.api import (
    RemoteEntitiesSearch,
    RemoteEntity,
)
from rero_ils.modules.holdings.api import Holding, HoldingsSearch
from rero_ils.modules.items.api import Item, ItemsSearch
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.locations.api import Location
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.utils import date_string_to_utc


def set_value(data, old_data, key):
    """Merge a single key from new data into old data if not already present.

    This function implements a non-destructive merge strategy, preserving
    existing values in old_data while adding missing keys from new data.
    Used primarily during entity source resolution to combine data from
    multiple authority sources (e.g., idref, gnd, rero).

    :param data: Source dictionary containing new values to merge.
    :type data: dict
    :param old_data: Target dictionary to be updated.
    :type old_data: dict
    :param key: The key to transfer from data to old_data.
    :type key: str
    :returns: The updated old_data dictionary. Modified in place and returned.
    :rtype: dict

    Example::

        old = {'name': 'John', 'age': 30}
        new = {'age': 25, 'city': 'Paris'}
        set_value(new, old, 'city')
        # Returns: {'name': 'John', 'age': 30, 'city': 'Paris'}
        set_value(new, old, 'age')  # Doesn't override existing
        # Returns: {'name': 'John', 'age': 30, 'city': 'Paris'}
    """
    value = data.get(key)
    if not old_data.get(key) and value:
        old_data[key] = value
    return old_data


def replace_contribution_sources(contribution, source_order):
    """Merge contribution entity data from multiple authority sources.

    This function resolves contribution entities by merging data from multiple
    authority control sources (e.g., idref, gnd, rero) according to language
    preferences. It implements a priority-based merge where the first source
    in source_order takes precedence.

    The merge process:

    1. Iterates through sources in the specified order (language-dependent)
    2. For each source found, extracts authority control data
    3. Creates a reference list with source and PID information
    4. Merges entity fields (name, dates, qualifiers) using set_value
    5. Removes raw source data and attaches resolved refs

    Entity fields processed:

    - Basic: type, preferred_name, numeration, qualifier
    - Dates: date_of_birth, date_of_death
    - Organisation: subordinate_unit
    - Conference: conference, conference_number, conference_date, conference_place

    :param contribution: Contribution dictionary containing an 'entity' key
        with source-specific data (idref, gnd, rero, etc.).
    :type contribution: dict
    :param source_order: Ordered list of source identifiers (e.g., ['idref', 'gnd'])
        defining merge priority. Sources earlier in the list have higher priority.
    :type source_order: list
    :returns: The contribution dictionary with entity data merged and refs added.
        The 'entity' now contains merged fields from all sources and
        refs (list of {'source': str, 'pid': str} dictionaries).
    :rtype: dict

    Example::

        contribution = {
            'entity': {
                'idref': {'pid': '12345', 'preferred_name': 'Doe, John'},
                'gnd': {'pid': '67890', 'date_of_birth': '1980'}
            }
        }
        replace_contribution_sources(contribution, ['idref', 'gnd'])
        # Returns merged entity with preferred_name from idref and date_of_birth from gnd
    """
    refs = []
    entity = contribution.get("entity")
    for source in source_order:
        if source_data := entity.get(source):
            refs.append({"source": source, "pid": source_data["pid"]})
            for key in [
                "type",
                "preferred_name",
                "numeration",
                "qualifier",
                "date_of_birth",
                "date_of_death",
                "subordinate_unit",
                "conference",
                "conference_number",
                "conference_date",
                "conference_place",
            ]:
                entity = set_value(source_data, entity, key)
            entity.pop(source)
    entity["refs"] = refs
    contribution["entity"] = entity
    return contribution


def replace_concept_sources(concept, source_order):
    """Merge concept/subject entity data from multiple thesaurus sources.

    Similar to replace_contribution_sources but for subject/concept entities
    from thesauri (e.g., rameau, lcsh, mesh). Merges data according to
    language-specific source preferences.

    Concept fields processed:

    - type: Entity type (Topic, Place, Temporal, etc.)
    - authorized_access_point: Preferred subject heading term

    :param concept: Concept entity dictionary with source-specific data.
    :type concept: dict
    :param source_order: Ordered list of thesaurus sources (e.g., ['rameau', 'lcsh'])
        defining merge priority.
    :type source_order: list
    :returns: The concept entity with merged data and refs list containing
        source/PID information for each thesaurus.
    :rtype: dict

    Example::

        concept = {
            'rameau': {'pid': 'sh85001', 'authorized_access_point': 'Art'},
            'lcsh': {'pid': '123456'}
        }
        replace_concept_sources(concept, ['rameau', 'lcsh'])
        # Returns merged concept with authorized_access_point from rameau
    """
    refs = []
    for source in source_order:
        if source_data := concept.get(source):
            refs.append({"source": source, "pid": source_data["pid"]})
            for key in ["type", "authorized_access_point"]:
                concept = set_value(source_data, concept, key)
            concept.pop(source)
    concept["refs"] = refs
    return concept


def do_contribution(contribution, source_order):
    """Transform contribution entity to MARC 21 subfield structure.

    Converts a RERO ILS contribution (author, contributor, etc.) into MARC 21
    subfield notation ready for fields 100, 110, 111, 700, 710, 711, 600, 610, 611.

    This function:

    1. Resolves entity references ($ref) by fetching from database
    2. Merges multi-source entity data based on language preferences
    3. Determines appropriate MARC field format (personal vs corporate)
    4. Creates subfield dictionary with proper MARC codes
    5. Adds authority control references ($0)

    MARC subfields generated:

    Person (X00):
        - $a: Preferred name (surname, forename)
        - $b: Numeration (e.g., "II", "III")
        - $c: Qualifier/title (e.g., "Jr.", "Sir")
        - $d: Dates (birth-death years)
        - $4: Relator codes (roles)
        - $0: Authority control numbers

    Organisation (X10/X11):
        - $a: Corporate/conference name
        - $b: Subordinate units
        - $n: Conference number
        - $d: Conference date
        - $c: Conference place
        - $4: Relator codes
        - $0: Authority control numbers

    :param contribution: Contribution object containing entity data or $ref
        to resolve, and role (list of relator codes, optional).
    :type contribution: dict
    :param source_order: Ordered source list for language-specific resolution
        (e.g., ['idref', 'gnd', 'rero']).
    :type source_order: list
    :returns: A 4-element tuple (result, entity_type, surname, conference) where
        result is MARC subfield dict or None, entity_type is EntityType constant,
        surname is True if personal name in surname-first format, conference is
        True if organisation is a conference.
    :rtype: tuple

    .. note::

        Returns (None, None, False, False) if entity cannot be found in database
        or if preferred_name/authorized_access_point is missing.

    Example::

        contribution = {
            'entity': {'pid': '12345', '$ref': '...'},
            'role': ['aut', 'edt']
        }
        result, entity_type, surname, conference = do_contribution(
            contribution, ['idref', 'gnd']
        )
        result
        # => {'__order__': ['a', 'd', '4', '4'], 'a': 'Doe, John',
        #     'd': '1980 - 2020', '4': ['aut', 'edt']}
    """
    roles = contribution.get("role", [])
    entity = contribution.get("entity")
    if pid := entity.get("pid"):
        # we have a $ref, get the real entity
        ref = entity.get("$ref")
        if entity_db := RemoteEntity.get_record_by_pid(pid):
            contribution = replace_contribution_sources(contribution={"entity": entity_db}, source_order=source_order)
            # We got an entity from db. Replace the used entity with this one.
            entity = contribution["entity"]
        else:
            error_print(f"No entity found for pid:{pid} {ref}")
            return None, None, False, False
    if not (preferred_name := entity.get("preferred_name")):
        preferred_name = entity.get(f"authorized_access_point_{to_marc21.language}")
    result = {}
    conference = False
    surname = False
    result = add_value(result, "a", preferred_name)
    entity_type = entity.get("type")
    if entity_type == EntityType.PERSON:
        if "," in preferred_name:
            surname = True
        result = add_value(result, "b", entity.get("numeration"))
        result = add_value(result, "c", entity.get("qualifier"))

        dates = " - ".join(
            [
                (entity["date_of_birth"][:4] if len(entity.get("date_of_birth", "")) > 3 else ""),
                (entity["date_of_death"][:4] if len(entity.get("date_of_death", "")) > 3 else ""),
            ]
        )
        if dates != " - ":
            result = add_value(result, "d", dates)

    elif entity_type == EntityType.ORGANISATION:
        if entity.get("conference"):
            conference = True
        result = add_values(result, "b", entity.get("subordinate_unit"))
        result = add_value(result, "n", entity.get("conference_number"))
        result = add_value(result, "d", entity.get("conference_date"))
        result = add_value(result, "c", entity.get("conference_place"))
    result = add_values(result, "4", roles)
    refs = entity.get("refs", [])
    if refs:
        result["0"] = []
    for ref in refs:
        result["__order__"].append("0")
        result["0"].append(f"({ref['source']}){ref['pid']}")
    return result, entity_type, surname, conference


def resolve_entity(entity, source_order):
    """Resolve entity $ref and merge multi-source data.

    Fetches entity data from the database if a $ref is present, then merges
    data from multiple authority sources according to language preferences.
    This is the base resolution step used by do_concept and other entity
    processing functions.

    :param entity: Entity dictionary that may contain pid (indicates a $ref),
        $ref (reference URL), source-specific data (idref, gnd, rameau, etc.),
        or authorized_access_point (direct access point if no $ref).
    :type entity: dict
    :param source_order: Ordered list of authority sources defining merge
        priority (e.g., ['idref', 'gnd'] or ['rameau', 'lcsh']).
    :type source_order: list
    :returns: A 2-element tuple (resolved_entity, from_db) where resolved_entity
        is the merged entity dict or None if $ref cannot be resolved, and
        from_db is True if entity was fetched from database.
    :rtype: tuple

    Example::

        entity = {'pid': '12345', '$ref': '...'}
        resolved, from_db = resolve_entity(entity, ['rameau', 'lcsh'])
        resolved['authorized_access_point']
        # => 'Art -- France'
        resolved['refs']
        # => [{'source': 'rameau', 'pid': '12345'}]
    """
    if pid := entity.get("pid"):
        ref = entity.get("$ref")
        # we have a $ref, get the real entity
        if resolved := RemoteEntity.get_record_by_pid(pid):
            resolved = replace_concept_sources(concept=resolved, source_order=source_order)
            return resolved, True
        error_print(f"No entity found for pid:{pid} {ref}")
        return None, False
    return entity, False


def do_concept(entity, source_order):
    """Transform subject/concept entity to MARC 21 subfield structure.

    Converts a RERO ILS subject/concept entity into MARC 21 subfield notation
    for fields 6XX and 655 (subject access points).

    Process:

    1. Resolves entity $ref if present
    2. Merges multi-source thesaurus data
    3. Extracts authorized access point
    4. Creates MARC subfield dictionary
    5. Adds authority control references ($0) if available

    :param entity: Subject/concept entity containing pid (if $ref), $ref
        (reference URL), authorized_access_point (subject heading term),
        or authorized_access_point_{lang} (language-specific variant).
    :type entity: dict
    :param source_order: Ordered thesaurus source list for language-specific
        resolution (e.g., ['rameau', 'lcsh', 'mesh']).
    :type source_order: list
    :returns: MARC subfield dictionary with __order__ (list of subfield codes),
        a (authorized access point), and 0 (authority control numbers if refs
        available). Returns None if entity cannot be resolved or has no access point.
    :rtype: dict or None

    Example::

        entity = {'pid': '67890', '$ref': '...'}
        do_concept(entity, ['rameau', 'lcsh'])
        # Returns: {'__order__': ['a', '0'], 'a': 'Architecture -- France', '0': ['(rameau)67890']}
    """
    resolved_entity, from_db = resolve_entity(entity, source_order)
    if resolved_entity is None:
        return None

    if from_db:
        authorized_access_point = resolved_entity.get("authorized_access_point")
    else:
        authorized_access_point = resolved_entity.get(
            f"authorized_access_point_{to_marc21.language}"
        ) or resolved_entity.get("authorized_access_point")
    result = {}
    if not authorized_access_point:
        return None
    result = add_value(result, "a", authorized_access_point)
    if refs := resolved_entity.get("refs", []):
        result["0"] = []
        for ref in refs:
            result["__order__"].append("0")
            result["0"].append(f"({ref['source']}){ref['pid']}")
    return result


def get_holdings_items(document_pid, organisation_pids=None, library_pids=None, location_pids=None):
    """Retrieve holdings and items data for a document with institutional context.

    Fetches all holdings and items associated with a document, enriched with
    organisation, library, and location information. Supports filtering to
    include only holdings/items from specific institutions.

    This function:

    1. Finds all holdings for the document (excluding masked)
    2. Applies optional filters (organisation/library/location)
    3. Batch-fetches institutional metadata (caching names)
    4. For standard holdings, retrieves associated items
    5. Structures data for MARC 949 field serialization

    Holdings types:

    - standard: Physical holdings with items (books, etc.)
    - electronic: Electronic holdings without items
    - serial: Serial holdings with patterns

    :param document_pid: PID of the document to retrieve holdings for.
    :type document_pid: str
    :param organisation_pids: Filter by organisation PIDs. Only holdings from
        these organisations will be included. Defaults to None (no filtering).
    :type organisation_pids: list, optional
    :param library_pids: Filter by library PIDs. Only holdings from these
        libraries will be included. Defaults to None (no filtering).
    :type library_pids: list, optional
    :param location_pids: Filter by location PIDs. Only holdings from these
        locations will be included. Defaults to None (no filtering).
    :type location_pids: list, optional
    :returns: List of dictionaries containing organisation, library, location,
        holdings data, and item data (for standard holdings only).
    :rtype: list

    .. note::

        - Institutional names are cached during processing to minimize database queries
        - Each item gets its own result entry (holdings replicated per item)
        - Electronic/serial holdings appear once without item data
        - Only unmasked holdings and items are included

    Example::

        holdings = get_holdings_items(
            document_pid='doc123',
            organisation_pids=['org1'],
            library_pids=['lib2']
        )
        len(holdings)
        # => 3  # Holdings from org1/lib2 with their items
    """

    def get_name(resource, pid):
        """Fetch resource name by PID.

        Helper function to retrieve the name field from a resource.
        Called within get_holdings_items where names are cached in
        dictionaries to avoid redundant database queries.

        :param resource: Resource API class (Organisation, Library, or Location).
        :type resource: class
        :param pid: Persistent identifier of the resource.
        :type pid: str
        :returns: The resource's name field, or None if not found.
        :rtype: str or None
        """
        data = resource.get_record_by_pid(pid)
        if data:
            return data.get("name")
        return None

    results = []
    if document_pid:
        holding_pids = Holding.get_holdings_pid_by_document_pid(document_pid=document_pid, with_masked=False)

        holding_pids = list(holding_pids)
        organisations = {}
        libraries = {}
        locations = {}
        query = HoldingsSearch().filter("terms", pid=holding_pids)
        if organisation_pids:
            query = query.filter({"terms": {"organisation.pid": organisation_pids}})
        if library_pids:
            query = query.filter({"terms": {"library.pid": library_pids}})
        if location_pids:
            query = query.filter({"terms": {"location.pid": location_pids}})
        for hit in query.scan():
            holding = hit.to_dict()
            organisation_pid = hit.organisation.pid
            if organisation_pid not in organisations:
                organisations[organisation_pid] = get_name(Organisation, organisation_pid)
            library_pid = hit.library.pid
            if library_pid not in libraries:
                libraries[library_pid] = get_name(Library, library_pid)
            location_pid = hit.location.pid
            if location_pid not in locations:
                locations[location_pid] = get_name(Location, location_pid)

            result = {
                "organisation": {
                    "pid": organisation_pid,
                    "name": organisations[organisation_pid],
                },
                "library": {"pid": library_pid, "name": libraries[library_pid]},
                "location": {"pid": location_pid, "name": locations[location_pid]},
                "holdings": {
                    "call_number": holding.get("call_number"),
                    "second_call_number": holding.get("second_call_number"),
                    "enumerationAndChronology": holding.get("enumerationAndChronology"),
                    "electronic_location": holding.get("electronic_location", []),
                    "notes": holding.get("notes", []),
                    "supplementaryContent": holding.get("supplementaryContent"),
                    "index": holding.get("index"),
                    "missing_issues": holding.get("missing_issues"),
                },
            }
            if hit.holdings_type == "standard":
                item_pids = Item.get_items_pid_by_holding_pid(hit.pid, with_masked=False)
                item_hits = ItemsSearch().filter("terms", pid=list(item_pids)).scan()
                for item_hit in item_hits:
                    item_data = item_hit.to_dict()
                    item_result = dict(result)
                    item_result["item"] = {
                        "barcode": item_data.get("barcode"),
                        "all_number": item_data.get("all_number"),
                        "second_call_number": item_data.get("second_call_number"),
                        "enumerationAndChronology": item_data.get("enumerationAndChronology"),
                        "url": item_data.get("url"),
                        "notes": item_data.get("notes", []),
                    }
                    results.append(item_result)
            else:
                results.append(result)
    return results


ORDER = [
    "leader",
    "pid",
    "date_and_time_of_latest_transaction",
    "fixed_length_data_elements",
    "identifiedBy",
    "title_responsibility",
    "provisionActivity",
    "copyrightDate",
    "physical_description",
    "general_notes",
    "table_of_contents",
    "summary",
    "dissertation",
    "subjects",
    "genreForm",
    "contribution",
    "type",
    "holdings_items",
]

#: MARC21 Leader positions and their meanings:
#: - 00-04: Record length (system-generated)
#: - 05: Record status (n=new, c=corrected, d=deleted, a=increase encoding level)
#: - 06: Type of record (a=language material, c=notated music, e=cartographic, etc.)
#: - 07: Bibliographic level (m=monograph, s=serial, a=article, c=collection)
#: - 08-09: Type of control and character encoding scheme
#: - 10: Indicator count (always 2)
#: - 11: Subfield code count (always 2)
#: - 12-16: Base address of data (system-generated)
#: - 17: Encoding level (blank=full, 1=full not examined, etc.)
#: - 18: Descriptive cataloging form (a=AACR2, i=ISBD, c=ISBD w/o punctuation)
#: - 19: Multipart resource record level
#: - 20-23: Entry map (always "4500")
LEADER_DEFAULT = "00000cam a2200000zu 4500"

#: Mapping of document main_type to MARC leader position 06 (Type of record)
TYPE_OF_RECORD_MAP = {
    "docmaintype_book": "a",  # Language material
    "docmaintype_article": "a",  # Language material
    "docmaintype_serial": "a",  # Language material (serials handled via pos 07)
    "docmaintype_audio": "i",  # Nonmusical sound recording
    "docmaintype_music": "j",  # Musical sound recording
    "docmaintype_score": "c",  # Notated music
    "docmaintype_video": "g",  # Projected medium (video)
    "docmaintype_movie": "g",  # Projected medium (film)
    "docmaintype_image": "k",  # Two-dimensional nonprojectable graphic
    "docmaintype_map": "e",  # Cartographic material
    "docmaintype_game": "r",  # Three-dimensional artifact
    "docmaintype_kit": "o",  # Kit
    "docmaintype_software": "m",  # Computer file
    "docmaintype_file": "m",  # Computer file
    "docmaintype_other": "a",  # Default to language material
}

#: Mapping of document main_type to MARC leader position 07 (Bibliographic level)
BIBLIOGRAPHIC_LEVEL_MAP = {
    "docmaintype_serial": "s",  # Serial
    "docmaintype_article": "a",  # Monographic component part
    "docmaintype_book": "m",  # Monograph
    # Default to monograph for others
}


def generate_leader(document):
    """Generate dynamic MARC 21 leader string based on document characteristics.

    Creates a properly formatted 24-character MARC 21 leader with document-specific
    values for type of record (position 06) and bibliographic level (position 07).
    This replaces static leader generation with intelligent type detection.

    Leader positions modified:

    - Position 06 (Type of record): Set based on document main_type
      (a=language material, c=notated music, e=cartographic, g=video, etc.)
    - Position 07 (Bibliographic level): Set based on document main_type
      (m=monograph, s=serial, a=article component)

    Special handling:

    - Electronic resources: If contentMediaCarrier indicates computer media
      (rdamedia:c) and the document is language material, position 06 changes
      to 'm' (computer file)

    :param document: RERO ILS document dictionary containing type (list of type
        objects with main_type field) and contentMediaCarrier (list with mediaType
        information, optional).
    :type document: dict
    :returns: A 24-character MARC 21 leader string. Defaults to monograph/language
        material ("00000cam a2200000zu 4500") if type information is missing.
    :rtype: str

    .. note::

        System-generated positions (00-04: record length, 12-16: base address)
        remain as zeros and will be filled by the MARC serialization system.

    Example::

        doc = {'type': [{'main_type': 'docmaintype_serial'}]}
        generate_leader(doc)
        # Returns: '00000cas a2200000zu 4500'  # Position 07 = 's' for serial

        doc = {
            'type': [{'main_type': 'docmaintype_video'}],
        }
        generate_leader(doc)
        # Returns: '00000cgm a2200000zu 4500'  # Position 06 = 'g' for video
    """
    # Start with default leader template
    leader = list(LEADER_DEFAULT)

    # Get document type information
    doc_types = document.get("type", [])
    main_type = None
    for doc_type in doc_types:
        if mt := doc_type.get("main_type"):
            main_type = mt
            break

    if main_type:
        # Position 06: Type of record
        type_of_record = TYPE_OF_RECORD_MAP.get(main_type, "a")
        leader[6] = type_of_record

        # Position 07: Bibliographic level
        bib_level = BIBLIOGRAPHIC_LEVEL_MAP.get(main_type, "m")
        leader[7] = bib_level

    # Check for electronic resources
    content_media = document.get("contentMediaCarrier", [])
    for cmc in content_media:
        if cmc.get("mediaType") == "rdamedia:c":  # computer
            # If it's computer media and language material, mark as computer file
            if leader[6] == "a":
                leader[6] = "m"
            break

    return "".join(leader)


class ToMarc21Overdo(Underdo):
    """DoJSON Overdo extension for RERO ILS to MARC 21 transformation.

    This class extends DoJSON's Underdo (reverse transformation) to convert
    RERO ILS internal JSON documents to MARC 21 format. It provides:

    - Pre-processing hooks for leader and 008 field generation
    - Entity resolution with language-aware source ordering
    - Holdings/items inclusion (field 949)
    - Physical description normalization
    - Note type segregation
    - Custom field ordering

    The do() method orchestrates the complete transformation pipeline:

    1. Generate dynamic leader based on document type
    2. Create fixed-length data elements (008 field)
    3. Add timestamp (005 field)
    4. Normalize title with responsibility statement
    5. Resolve contribution entities with source preferences
    6. Process physical description and notes
    7. Optionally fetch holdings/items
    8. Apply field ordering
    9. Execute DoJSON transformation rules

    :ivar responsibility_statement: Cache for responsibility statements.
    :vartype responsibility_statement: dict
    :ivar language: Target language for entity resolution.
    :vartype language: str
    :ivar source_order: Ordered list of authority sources for entity resolution.
    :vartype source_order: list

    .. seealso::

        DoJSON Underdo: https://dojson.readthedocs.io/en/latest/api.html#underdo
    """

    responsibility_statement = {}

    def do(
        self,
        blob,
        language="en",
        ignore_missing=True,
        exception_handlers=None,
        with_holdings_items=False,
        organisation_pids=None,
        library_pids=None,
        location_pids=None,
    ):
        """Transform RERO ILS JSON document to MARC 21 format.

        This is the main entry point for the transformation. It pre-processes
        the document, applies DoJSON transformation rules, and returns a
        MARC 21 representation.

        Pre-processing steps:

        1. **Leader generation**: Creates dynamic leader based on document type
        2. **Fixed field creation**: Builds 008 field with creation date (positions
           00-05), publication dates (positions 07-14), fiction indicator (position
           33), and language code (positions 35-37)
        3. **Timestamp addition**: Adds 005 field with last modification time
        4. **Title normalization**: Combines title and responsibility statement
        5. **Entity source ordering**: Sets language-specific authority preferences
        6. **Holdings inclusion**: Optionally fetches holdings/items (field 949)
        7. **Physical description**: Merges extent, duration, dimensions, formats
        8. **Note segregation**: Separates general notes from special note types
        9. **Field ordering**: Applies MARC logical order (leader → 00X → 9XX)

        :param blob: RERO ILS document dictionary to transform containing pid,
            _created, _updated, type, title, contribution, subjects, etc.
        :type blob: dict
        :param language: Target language for entity resolution. Affects which
            authority sources are preferred (e.g., 'fr' prefers idref, 'de'
            prefers gnd). Defaults to 'en'.
        :type language: str, optional
        :param ignore_missing: If False, raises MissingRule exception when a JSON
            key has no matching transformation rule. Defaults to True.
        :type ignore_missing: bool, optional
        :param exception_handlers: Custom exception handlers for non-standard
            field processing. Defaults to None.
        :type exception_handlers: dict, optional
        :param with_holdings_items: Whether to include holdings and items in
            field 949. Warning: time-consuming for documents with many holdings.
            Defaults to False.
        :type with_holdings_items: bool, optional
        :param organisation_pids: Filter holdings by organisation PIDs. Only
            applicable if with_holdings_items=True. Defaults to None.
        :type organisation_pids: list, optional
        :param library_pids: Filter holdings by library PIDs. Only applicable
            if with_holdings_items=True. Defaults to None.
        :type library_pids: list, optional
        :param location_pids: Filter holdings by location PIDs. Only applicable
            if with_holdings_items=True. Defaults to None.
        :type location_pids: list, optional
        :returns: MARC 21 record with fields as keys (e.g., 'leader', '001',
            '245__', '700__'). Includes __order__ key for field sequence.
        :rtype: GroupableOrderedDict
        :raises MissingRule: If ignore_missing=False and a field has no
            transformation rule.

        .. note::

            - The 008 field uses '|' for undefined positions and 'x' for unknown values
            - Holdings/items inclusion can significantly increase processing time
            - Entity resolution requires network calls to authority databases

        Example::

            converter = ToMarc21Overdo()
            rero_doc = {'pid': '123', 'title': [...], ...}
            marc_record = converter.do(
                rero_doc,
                language='fr',
                with_holdings_items=True,
                organisation_pids=['org1']
            )
            marc_record['245__']
            # => {'a': 'Title', 'b': 'Subtitle', 'c': 'Author', ...}
        """
        # Generate dynamic MARC leader (24 chars) based on document type.
        # Sets position 06 (type of record) and 07 (bibliographic level) intelligently.
        self.language = language
        blob["leader"] = generate_leader(blob)

        # Build 008 fixed-length data elements (40 characters):
        # Positions 00-05: Date entered (yymmdd format)
        # Position 06: Type of date/publication status (filled below)
        # Positions 07-14: Date 1 and Date 2 (publication dates)
        # Position 33: Literary form (fiction indicator)
        # Positions 35-37: Language code
        created = date_string_to_utc(blob["_created"]).strftime("%y%m%d")
        fixed_data = f"{created}|||||||||xx#|||||||||||||||||||||c"
        # Set position 33 (Literary form): 0=non-fiction, 1=fiction
        fiction = blob.get("fiction_statement")
        if fiction == DocumentFictionType.Fiction.value:
            fixed_data = f"{fixed_data[:33]}1{fixed_data[34:]}"
        elif fiction == DocumentFictionType.NonFiction.value:
            fixed_data = f"{fixed_data[:33]}0{fixed_data[34:]}"
        # Extract publication dates from provisionActivity for positions 07-14.
        # Position 06 (type of date): s=single, m=multiple (range)
        provision_activity = blob.get("provisionActivity", [])
        for p_activity in provision_activity:
            if p_activity.get("type") == "bf:Publication":
                end_date = str(p_activity.get("endDate", ""))
                if end_date:
                    fixed_data = f"{fixed_data[:11]}{end_date}{fixed_data[15:]}"
                if start_date := str(p_activity.get("startDate", "")):
                    type_of_date = "s"
                    if end_date:
                        type_of_date = "m"
                    fixed_data = f"{fixed_data[:6]}{type_of_date}{start_date}{fixed_data[11:]}"
                    break
        # Set positions 35-37: Language code (ISO 639-2/B)
        if doc_languages := utils.force_list(blob.get("language")):
            lang_code = doc_languages[0].get("value")
            if lang_code and len(lang_code) == 3:
                fixed_data = f"{fixed_data[:35]}{lang_code}{fixed_data[38:]}"
        blob["fixed_length_data_elements"] = fixed_data

        # Add 005 field: date and time of latest transaction (YYYYMMDDHHmmss.f)
        updated = date_string_to_utc(blob["_updated"])
        blob["date_and_time_of_latest_transaction"] = updated.strftime("%Y%m%d%H%M%S.0")

        # Add responsibilityStatement to title
        if blob.get("title"):
            blob["title_responsibility"] = {
                "titles": blob.get("title", {}),
                "responsibility": " ; ".join(create_title_responsibilites(blob.get("responsibilityStatement", []))),
            }
        # Configure language-specific authority source ordering.
        # RERO_ILS_AGENTS_LABEL_ORDER defines which authority sources to prefer
        # for each language (e.g., French prefers idref, German prefers gnd).
        # Try to get from Flask app context first, fall back to direct import
        # for CLI usage (where no app context exists).
        try:
            order = current_app.config.get("RERO_ILS_AGENTS_LABEL_ORDER", {})
        except RuntimeError:
            from rero_ils.config import RERO_ILS_AGENTS_LABEL_ORDER as order
        self.source_order = order.get(self.language, order.get(order.get("fallback", "en"), []))

        if with_holdings_items:
            # Fetch holdings and items for field 949 (local holdings data).
            # Warning: This can be time-consuming for documents with many holdings.
            # Results are filtered by organisation/library/location if specified.
            blob["holdings_items"] = get_holdings_items(
                document_pid=blob.get("pid"),
                organisation_pids=organisation_pids,
                library_pids=library_pids,
                location_pids=location_pids,
            )

        # Build 300 field (Physical Description) by combining multiple sources:
        # - $a: extent (with duration if not already included)
        # - $b: other physical details (production method, color, illustrations)
        # - $c: dimensions (including book formats)
        # - $e: accompanying material
        physical_description = {}
        extent = blob.get("extent")
        durations = ", ".join(blob.get("duration", []))
        if extent:
            if (durations and f"({durations})" in extent) or not durations:
                physical_description["extent"] = extent
            else:
                physical_description["extent"] = f"{extent} ({durations})"
        note = blob.get("note", [])
        other_physical_details = []
        other_physical_details.extend(value["label"] for value in note if value["noteType"] == "otherPhysicalDetails")
        if not other_physical_details:
            other_physical_details.extend(translate(value) for value in blob.get("productionMethod", []))
            other_physical_details.extend(iter(blob.get("illustrativeContent", [])))
            other_physical_details.extend(translate(value) for value in blob.get("colorContent", []))
        if other_physical_details:
            physical_description["other_physical_details"] = " ; ".join(other_physical_details)
        if accompanying_material := " ; ".join(
            [v.get("label") for v in note if v["noteType"] == "accompanyingMaterial"]
        ):
            physical_description["accompanying_material"] = accompanying_material
        dimensions = blob.get("dimensions", [])
        book_formats = blob.get("bookFormat", [])
        upper_book_formats = [v.upper() for v in book_formats]
        new_dimensions = []
        for dimension in dimensions:
            try:
                index = upper_book_formats.index(dimension.upper())
                new_dimensions.append(book_formats[index])
                del book_formats[index]
            except ValueError:
                new_dimensions.append(dimension)
        new_dimensions.extend(iter(book_formats))
        if new_dimensions:
            physical_description["dimensions"] = " ; ".join(new_dimensions)

        if physical_description:
            blob["physical_description"] = physical_description

        # Extract general notes for field 500 (excluding specialized note types).
        # Note types handled elsewhere:
        # - otherPhysicalDetails, accompanyingMaterial → 300$b, 300$e
        # - dissertation → 502
        # - summary → 520
        # - tableOfContents → 505
        general_notes = []
        for n in note:
            if n["noteType"] == "general":
                general_notes.append(n["label"])
        if general_notes:
            blob["general_notes"] = general_notes

        # Table of contents is already in the correct format (array of strings)
        if table_of_contents := blob.get("tableOfContents"):
            blob["table_of_contents"] = table_of_contents

        # Apply MARC field ordering defined in ORDER constant.
        # This ensures fields appear in standard MARC order:
        # leader → 001-008 → 020-245 → 264-300 → 500-655 → 700-949
        keys = {}
        for key, value in blob.items():
            count = 1
            if isinstance(value, (list, set, tuple)):
                count = len(value)
            keys.setdefault(key, count - 1)
            keys[key] += 1
        order = []
        for key in ORDER:
            order.extend(key for _ in range(keys.get(key, 0)))
        blob["__order__"] = order
        return super().do(blob, ignore_missing=ignore_missing, exception_handlers=exception_handlers)


def add_value(result, sub_tag, value):
    """Add a single subfield to MARC field result dictionary.

    Appends subfield code to __order__ list and stores value.
    Used for non-repeatable subfields.

    :param result: MARC field dictionary being built.
    :type result: dict
    :param sub_tag: MARC subfield code (single character).
    :type sub_tag: str
    :param value: Subfield value to add.
    :type value: str
    :returns: The modified result dictionary.
    :rtype: dict
    """
    if value:
        result.setdefault("__order__", []).append(sub_tag)
        result[sub_tag] = value
    return result


def add_values(result, sub_tag, values):
    """Add multiple values for a repeatable subfield to MARC field result.

    Appends subfield code multiple times to __order__ list and stores
    values as a list. Used for repeatable subfields.

    :param result: MARC field dictionary being built.
    :type result: dict
    :param sub_tag: MARC subfield code (single character).
    :type sub_tag: str
    :param values: List of subfield values to add.
    :type values: list
    :returns: The modified result dictionary.
    :rtype: dict
    """
    if values:
        for _ in range(len(values)):
            result.setdefault("__order__", []).append(sub_tag)
        result[sub_tag] = values
    return result


to_marc21 = ToMarc21Overdo()


@to_marc21.over("leader", "^leader")
def reverse_leader(self, key, value):
    """Reverse - leader."""
    assert len(value) == 24
    return value


@to_marc21.over("001", "^pid")
def reverse_pid(self, key, value):
    """Reverse - pid."""
    return [value]


@to_marc21.over("005", "^date_and_time_of_latest_transaction")
def reverse_latest_transaction(self, key, value):
    """Reverse - date and time of latest transaction."""
    return value


@to_marc21.over("008", "^fixed_length_data_elements")
def reverse_fixed_length_data_elements(self, key, value):
    """Reverse - fixed length data elements."""
    return [value]


@to_marc21.over("02X", "^identifiedBy")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_identified_by(self, key, value):
    """Reverse - identified by."""
    status = value.get("status")
    qualifier = value.get("qualifier")
    identified_by_type = value["type"]
    identified_by_value = value["value"]
    result = {}
    if identified_by_type == "bf:Isbn":
        subfield = "z" if status else "a"
        result["__order__"] = [subfield]
        result[subfield] = identified_by_value
        if qualifier:
            result["__order__"].append("q")
            result["q"] = qualifier
        self.append(("020__", utils.GroupableOrderedDict(result)))
    return


@to_marc21.over("245", "^title_responsibility")
@utils.ignore_value
def reverse_title(self, key, value):
    """Reverse - title."""

    def get_part(parts, new_parts):
        """Create part list."""
        for part in new_parts:
            part_numbers = []
            for part_number in part.get("partNumber", []):
                language = part_number.get("language", "default")
                if display_alternate_graphic_first(language):
                    part_numbers.insert(0, part_number["value"])
                else:
                    part_numbers.append(part_number["value"])
            part_names = []
            for part_name in part.get("partName", []):
                language = part_name.get("language", "default")
                if display_alternate_graphic_first(language):
                    part_names.insert(0, part_name["value"])
                else:
                    part_names.append(part_name["value"])
            parts.append(
                {
                    "part_number": ". ".join(part_numbers),
                    "part_name": ". ".join(part_names),
                }
            )
        return parts

    result = None
    titles = value.get("titles")
    responsibility = value.get("responsibility")
    main_titles = []
    sub_titles = []
    main_titles_parallel = []
    sub_titles_parallel = []
    parts = []
    for title in titles:
        if title.get("type") == "bf:Title":
            for main_title in title.get("mainTitle"):
                if display_alternate_graphic_first(main_title.get("language", "default")):
                    main_titles.insert(0, main_title["value"])
                else:
                    main_titles.append(main_title["value"])
            for sub_title in title.get("subtitle", []):
                if display_alternate_graphic_first(sub_title.get("language", "default")):
                    sub_titles.insert(0, sub_title["value"])
                else:
                    sub_titles.append(sub_title["value"])
        if title.get("type") == "bf:ParallelTitle":
            for main_title in title.get("mainTitle"):
                if display_alternate_graphic_first(main_title.get("language", "default")):
                    main_titles_parallel.insert(0, main_title["value"])
                else:
                    main_titles_parallel.append(main_title["value"])
            for sub_title in title.get("subtitle", []):
                if display_alternate_graphic_first(sub_title.get("language", "default")):
                    sub_titles_parallel.insert(0, sub_title["value"])
                else:
                    sub_titles_parallel.append(sub_title["value"])
        parts = get_part(parts, title.get("part", []))

    result = {"__order__": ["a"], "$ind1": "0", "a": ". ".join(main_titles)}
    if sub_titles:
        result["__order__"].append("b")
        result["b"] = ". ".join(sub_titles)
    if main_titles_parallel:
        if result.get("b"):
            result["b"] += f" = {'. '.join(main_titles_parallel)}"
        else:
            result["__order__"].append("b")
            result["b"] = ". ".join(main_titles_parallel)
    if sub_titles_parallel:
        if result.get("b"):
            result["b"] += f" : {'. '.join(sub_titles_parallel)}"
        else:
            result["__order__"].append("b")
            result["b"] = ". ".join(sub_titles_parallel)
    if responsibility:
        result["__order__"].append("c")
        result["c"] = responsibility
    for part in parts:
        part_number = part.get("part_number")
        if part_number:
            result["__order__"].append("n")
            result.setdefault("n", [])
            result["n"].append(part_number)
        part_name = part.get("part_name")
        if part_name:
            result["__order__"].append("p")
            result.setdefault("p", [])
            result["p"].append(part_name)

    return result or None


@to_marc21.over("264", "^(provisionActivity|copyrightDate)")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_provision_activity(self, key, value):
    """Reverse - provisionActivity."""
    # Pour chaque objet de "provisionActivity" (répétitif), créer une 264:
    # * si type=bf:Publication, ind2=1
    #     * sinon si type=bf:Distribution, ind2=2
    #         * sinon si type=bf:Manufacture, ind2=3
    #             * sinon si type=bf:Production, ind2=0
    # * prendre dans l'ordre chaque chaque objet de "statement"
    #     * $a = [label] si type=bf:Place
    #     * $a = [label] si type=bf:Agent
    #     * $a = [label] si type=bf:Date
    # Pour chaque "copyrightDate":
    # * 264 ind2=4 $a = [copyrightDate]
    if key == "copyrightDate":
        result = {
            "$ind2": "4",
        }
        return add_value(result, "a", value)
    data = {}
    order = []
    for statement in value.get("statement", []):
        statement_type = statement.get("type")
        subfield = "a"
        if statement_type == "bf:Agent":
            subfield = "b"
        elif statement_type == "Date":
            subfield = "c"
        for label in statement.get("label"):
            order.append(subfield)
            data.setdefault(subfield, [])
            data[subfield].append(label["value"])
            # only take the first label
            break
    if data:
        provision_activity_type = value.get("type")
        ind2 = ""
        if provision_activity_type == "bf:Publication":
            ind2 = "1"
        elif provision_activity_type == "bf:Distribution":
            ind2 = "2"
        elif provision_activity_type == "bf:Manufacture":
            ind2 = "3"
        elif provision_activity_type == "bf:Production":
            ind2 = "0"
        result = {"$ind2": ind2}
        for key, value in data.items():
            result = add_values(result, key, value)
        result["__order__"] = order
        return result
    return None


@to_marc21.over("300", "^physical_description")
@utils.ignore_value
def reverse_physical_description(self, key, value):
    """Reverse - physical_description."""
    result = {}
    add_value(result, "a", value.get("extent"))
    add_value(result, "b", value.get("other_physical_details"))
    add_value(result, "c", value.get("dimensions"))
    add_value(result, "e", value.get("accompanying_material"))
    return result or None


@to_marc21.over("500", "^general_notes")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_general_notes(self, key, value):
    """Reverse - general notes to MARC 500.

    MARC 500 - General Note (Repeatable)
    $a - General note (Not repeatable)

    Maps document general notes to MARC 500 fields.
    """
    if value:
        return {"__order__": ["a"], "a": value}
    return None


@to_marc21.over("502", "^dissertation")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_dissertation(self, key, value):
    """Reverse - dissertation note to MARC 502.

    MARC 502 - Dissertation Note (Repeatable)
    $a - Dissertation note (Not repeatable)

    Maps dissertation information to MARC 502 fields.
    Each dissertation entry may have multiple language labels.
    """
    if labels := value.get("label"):
        # Take the first label value (primary language)
        for label in labels:
            if label_value := label.get("value"):
                return {"__order__": ["a"], "a": label_value}
    return None


@to_marc21.over("505", "^table_of_contents")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_table_of_contents(self, key, value):
    """Reverse - table of contents to MARC 505.

    MARC 505 - Formatted Contents Note (Repeatable)
    $a - Formatted contents note (Not repeatable)
    Indicator 1: 0 = Contents, 1 = Incomplete contents, 2 = Partial contents
    Indicator 2: blank = Basic, 0 = Enhanced

    Maps tableOfContents entries to MARC 505 fields.
    """
    if value:
        return {"__order__": ["a"], "$ind1": "0", "a": value}
    return None


@to_marc21.over("520", "^summary")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_summary(self, key, value):
    """Reverse - summary/abstract to MARC 520.

    MARC 520 - Summary, Etc. (Repeatable)
    $a - Summary, etc. (Not repeatable)
    $c - Assigning source (Not repeatable)
    Indicator 1: blank = Summary, 0 = Subject, 1 = Review, 2 = Scope, 3 = Abstract

    Maps document summaries to MARC 520 fields.
    """
    result = {}
    if labels := value.get("label"):
        # Concatenate all language variants, taking the first value
        for label in labels:
            if label_value := label.get("value"):
                result = add_value(result, "a", label_value)
                break
    if source := value.get("source"):
        result = add_value(result, "c", source)
    return result or None


@to_marc21.over("6XX", "^subjects")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_subjects(self, key, value):
    """Reverse - subjects.

    Sujet Personne > 600
    Sujet Organisation > 610 OU 611 Conference
    Sujet Concept > 650
    """

    def add_identified_by(result, identified_by):
        """Adds $2 and $0 to result."""
        result = add_value(result, "2", identified_by["type"].lower())
        return add_value(result, "0", identified_by["value"])

    if entity := value.get("entity"):
        tag = None
        entity_type = entity.get("type")
        if entity_pid := entity.get("pid"):
            query = RemoteEntitiesSearch().filter("term", pid=entity_pid)
            if query.count():
                entity_type = next(query.source("type").scan()).type
        if entity_type in [EntityType.PERSON, EntityType.ORGANISATION]:
            result, entity_type, surname, conference = do_contribution(
                contribution={"entity": entity}, source_order=to_marc21.source_order
            )
            if entity_type == EntityType.PERSON:
                tag = "6001_" if surname else "6000_"
            elif entity_type == EntityType.ORGANISATION:
                tag = "611__" if conference else "610__"
        elif entity_type == EntityType.TOPIC:
            result = do_concept(entity=entity, source_order=to_marc21.source_order)
            tag = "650__"
        elif entity_type == EntityType.WORK:
            # Resolve $ref if present to get full entity data with refs
            resolved_entity, from_db = resolve_entity(entity, to_marc21.source_order)
            if resolved_entity is None:
                return
            if from_db:
                authorized_access_point = resolved_entity.get("authorized_access_point")
            else:
                authorized_access_point = resolved_entity.get(
                    f"authorized_access_point_{to_marc21.language}"
                ) or resolved_entity.get("authorized_access_point")
            if authorized_access_point:
                result = {}
                result = add_value(result, "t", authorized_access_point)
                # Add identifiedBy if present (for non-$ref entities)
                if identified_by := resolved_entity.get("identifiedBy"):
                    result = add_identified_by(result, identified_by)
                # Add authority control numbers from refs (for $ref entities)
                if refs := resolved_entity.get("refs"):
                    result["0"] = []
                    for ref in refs:
                        result["__order__"].append("0")
                        result["0"].append(f"({ref['source']}){ref['pid']}")
                self.append(("600__", utils.GroupableOrderedDict(result)))
            return
        elif entity_type == EntityType.PLACE:
            # Resolve $ref if present to get full entity data with refs
            resolved_entity, from_db = resolve_entity(entity, to_marc21.source_order)
            if resolved_entity is None:
                return
            if from_db:
                authorized_access_point = resolved_entity.get("authorized_access_point")
            else:
                authorized_access_point = resolved_entity.get(
                    f"authorized_access_point_{to_marc21.language}"
                ) or resolved_entity.get("authorized_access_point")
            if authorized_access_point:
                result = {}
                result = add_value(result, "a", authorized_access_point)
                # Add identifiedBy if present (for non-$ref entities)
                if identified_by := resolved_entity.get("identifiedBy"):
                    result = add_identified_by(result, identified_by)
                # Add authority control numbers from refs (for $ref entities)
                if refs := resolved_entity.get("refs"):
                    result["0"] = []
                    for ref in refs:
                        result["__order__"].append("0")
                        result["0"].append(f"({ref['source']}){ref['pid']}")
                self.append(("651__", utils.GroupableOrderedDict(result)))
            return
        elif entity_type == EntityType.TEMPORAL:
            # Resolve $ref if present to get full entity data with refs
            resolved_entity, from_db = resolve_entity(entity, to_marc21.source_order)
            if resolved_entity is None:
                return
            if from_db:
                authorized_access_point = resolved_entity.get("authorized_access_point")
            else:
                authorized_access_point = resolved_entity.get(
                    f"authorized_access_point_{to_marc21.language}"
                ) or resolved_entity.get("authorized_access_point")
            if authorized_access_point:
                result = {}
                result = add_value(result, "a", authorized_access_point)
                # Add identifiedBy if present (for non-$ref entities)
                if identified_by := resolved_entity.get("identifiedBy"):
                    result = add_identified_by(result, identified_by)
                # Add authority control numbers from refs (for $ref entities)
                if refs := resolved_entity.get("refs"):
                    result["0"] = []
                    for ref in refs:
                        result["__order__"].append("0")
                        result["0"].append(f"({ref['source']}){ref['pid']}")
                self.append(("648_7", utils.GroupableOrderedDict(result)))
            return
        else:
            error_print(f"No entity type found: {entity}")
    if tag and result:
        self.append((tag, utils.GroupableOrderedDict(result)))


@to_marc21.over("655", "^genreForm")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_genre_form(self, key, value):
    """Reverse - genreForm.

    Genre / Forme > 655 - Genre ou forme
    """
    if value.get("entity"):
        if result := do_concept(entity=value.get("entity"), source_order=to_marc21.source_order):
            self.append(("655__", utils.GroupableOrderedDict(result)))


@to_marc21.over("7XX", "^contribution")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_contribution(self, key, value):
    """Reverse - contribution."""
    result, entity_type, surname, conference = do_contribution(contribution=value, source_order=to_marc21.source_order)
    tag = None
    if entity_type == EntityType.PERSON:
        tag = "7001_" if surname else "7000_"
    elif entity_type == EntityType.ORGANISATION:
        tag = "711__" if conference else "710__"
    if tag and result:
        self.append((tag, utils.GroupableOrderedDict(result)))


@to_marc21.over("900", "^type")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_type(self, key, value):
    """Reverse - type."""
    result = {"__order__": ["a"], "a": value.get("main_type")}
    if subtype_type := value.get("subtype"):
        result["__order__"] = ["a", "b"]
        result["b"] = subtype_type
    return result


@to_marc21.over("949", "^holdings_items")
@utils.reverse_for_each_value
@utils.ignore_value
def reverse_holdings_items(self, key, value):
    """Reverse - holdings or items."""
    note_types_to_display = [
        "general_note",
        "patrimonial_note",
        "provenance_note",
        "binding_note",
        "condition_note",
    ]
    result = {
        "__order__": ["0", "1", "2", "3", "4", "5"],
        "0": value["organisation"]["pid"],
        "1": value["organisation"]["name"],
        "2": value["library"]["pid"],
        "3": value["library"]["name"],
        "4": value["location"]["pid"],
        "5": value["location"]["name"],
    }
    holdings = value.get("holdings", {})
    add_value(result, "B", holdings.get("call_number"))
    add_value(result, "C", holdings.get("second_call_number"))
    add_value(result, "D", holdings.get("enumerationAndChronology"))
    uris = [data["uri"] for data in holdings.get("electronic_location")]
    add_values(result, "E", uris)
    if notes := [note["content"] for note in holdings.get("notes", []) if note["type"] in note_types_to_display]:
        add_values(result, "F", notes)
    add_value(result, "G", holdings.get("supplementaryContent"))
    add_value(result, "H", holdings.get("index"))
    add_value(result, "I", holdings.get("missing_issues"))

    item = value.get("item", {})
    add_value(result, "a", item.get("barcode"))
    add_value(result, "b", item.get("call_number"))
    add_value(result, "c", item.get("enumerationAndChronology"))
    add_value(result, "e", item.get("url"))
    if notes := [note["content"] for note in item.get("notes", []) if note["type"] in note_types_to_display]:
        add_values(result, "f", notes)

    return result
