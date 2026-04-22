# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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


"""CQL (Contextual Query Language) Parser for SRU.

This module provides a CQL 1.2 parser that translates CQL queries into
search index query strings. It supports the standard CQL features including
boolean operators, relation modifiers, sort specifications, and prefix
declarations.

The parser is adapted from the cheshire3 project:
    https://github.com/cheshire3/cheshire3
    Original Author: Rob Sanderson (azaroth@liv.ac.uk)
    Version: 2.0 (CQL 1.2)

Features:
    - Full CQL 1.2 syntax support
    - Boolean operators: AND, OR, NOT (PROX not supported)
    - Relations: =, <, >, <=, >=, <>, all, any
    - Sort specifications with ascending/descending modifiers
    - Relation modifiers: /relevant, /exact, /word, /ignoreCase
    - Dublin Core index mappings to search index fields
    - Prefix declarations for custom context sets

Example::

    from rero_ils.modules.sru.cql_parser import parse
    query = parse('dc.title all "python programming" sortBy dc.date/descending')
    search_query = query.to_search()
    sort_keys = query.get_search_sort()

See Also:
    - CQL Specification: http://www.loc.gov/standards/sru/cql/
    - SRU Standard: http://www.loc.gov/standards/sru/
"""

from io import StringIO
from shlex import shlex

from lxml import etree
from lxml.builder import ElementMaker

from ..utils import strip_chars

SERVER_CHOICE_RELATION = "="
SERVER_CHOICE_INDEX = "cql.serverchoice"

#: Canonical SRU schema URI for MARC XML records.
SRU_MARCXML_SCHEMA_URI = "info:srw/schema/1/marcxml-v1.1-light"

#: Canonical SRU schema URI for Dublin Core records.
SRU_DC_SCHEMA_URI = "info:srw/schema/1/dc-v1.1"

ORDER = ["=", ">", ">=", "<", "<=", "<>"]
MODIFIER_SEPARATOR = "/"
BOOLEANS = ["and", "or", "not", "prox"]
SORT_WORD = "sortby"

RESERVED_PREFIXES = {
    "srw": "http://www.loc.gov/zing/cql/srw-indexes/v1.0/",
    "cql": "info:srw/cql-context-set/1/cql-v1.2",
    "dc": "http://purl.org/dc/elements/1.1/",
}

#: Both CQL context set URIs that map to the built-in ``cql`` prefix.
#: v1.1 is kept for backward compatibility with clients that declare
#: ``>cql=info:srw/cql-context-set/1/cql-v1.1`` explicitly.
CQL_CONTEXT_SET_URIS = {
    "info:srw/cql-context-set/1/cql-v1.1",
    "info:srw/cql-context-set/1/cql-v1.2",
}

XCQL_NAMESPACE = "http://www.loc.gov/zing/cql/xcql/"

ERROR_ON_EMPTY_TERM = False  # index = ''
ERROR_ON_QUOTED_IDENTIFIER = False  # '/foo/bar' = ''
ERROR_ON_DUPLICATE_PREFIX = False  # >a=b >a=c ''
FULL_RESULT_SET_NAME_CHECK = True  # cql.rsn=a and cql.rsn=a    (mutant!)


#: CQL sort modifier to search index sort order mapping.
#: Maps CQL sort modifiers (e.g., /ascending, /descending) to search sort orders.
#: Supports both short form (/ascending) and prefixed form (/sort.ascending).
SEARCH_SORT_MODIFIERS = {
    "ascending": "asc",
    "descending": "desc",
    "sort.ascending": "asc",
    "sort.descending": "desc",
    "missinglow": "missinglow",
    "missinghigh": "missinghigh",
    "missingomit": "missingomit",
    "sort.missinglow": "missinglow",
    "sort.missinghigh": "missinghigh",
    "sort.missingomit": "missingomit",
}

#: Maps missing-value CQL sort modifiers to ES ``missing`` values per sort order.
#: Tuple layout: (asc_value, desc_value).
#: "missingomit" is unsupported by ES and falls back to "_last" for both orders.
_SORT_MISSING_MAP = {
    "missinglow": ("_first", "_last"),
    "missinghigh": ("_last", "_first"),
    "missingomit": ("_last", "_last"),
}

#: CQL sort index to Elasticsearch sortable field mapping.
#: Maps Dublin Core and custom indexes to ES fields suitable for sorting.
#: These fields should be keyword type or have doc_values enabled for
#: efficient sorting. Use '_relevance' to sort by search score.
SEARCH_SORT_INDEX_MAPPINGS = {
    "dc.title": "sort_title",
    "dc.date": "provisionActivity.startDate",
    "dc.creator": "facet_contribution_en",
    "dc.contributor": "facet_contribution_en",
    "dc.identifier": "identifiedBy.value.raw",
    "dc.subject": "facet_subject_en",
    "dc.type": "type.main_type",
    "dc.language": "language.value",
    "_relevance": "_score",
}

#: Supported CQL relation modifiers that are processed without error.
#: These modifiers are acknowledged by the parser. Most map to default
#: search index behavior (relevance scoring, word matching, case insensitivity).
#:
#: - ``relevant``: Use relevance scoring (default search behavior)
#: - ``exact``: Exact match semantics
#: - ``word``: Word-based matching (default search behavior)
#: - ``ignorecase``: Case-insensitive matching (default search behavior)
#: - ``string``: Treat search term as a string literal
SUPPORTED_RELATION_MODIFIERS = {
    "relevant": "relevant",
    "exact": "exact",
    "word": "word",
    "ignorecase": "ignorecase",
    "string": "string",
}

#: Unsupported CQL relation modifiers with explanatory messages.
#: When these modifiers are used, the parser raises Diagnostic 21 with
#: the corresponding explanation message.
UNSUPPORTED_RELATION_MODIFIERS = {
    "stem": "Stemming not configurable per-query",
    "phonetic": "Phonetic matching not available",
    "fuzzy": "Fuzzy matching not supported",
    "regexp": "Regular expressions not supported in CQL",
    "respectcase": "Case-sensitive search not supported",
    "isodate": "ISO date parsing not supported",
}

#: Dublin Core index to search index query mapping.
#: Maps standard Dublin Core elements and CQL indexes to search index
#: query expressions. Complex mappings may include boolean operators
#: and field constraints (e.g., filtering by contribution role).
#:
#: Standard DC elements: title, creator, contributor, date, description,
#: language, publisher, type, identifier, relation, coverage, format,
#: rights, source, subject.
#:
#: Custom extensions: organisation, library, location, subtype.
SEARCH_INDEX_MAPPINGS = {
    "cql.anywhere": SERVER_CHOICE_INDEX,
    "dc.anywhere": SERVER_CHOICE_INDEX,
    "dc.contributor": "contribution.role:("
    "ape OR aqt OR arc OR art OR aus OR aut OR chr OR cll OR cmp OR com OR "
    "drt OR dsr OR enj OR fmk OR inv OR ive OR ivr OR lbt OR lsa OR lyr OR "
    "pht OR pra OR prg OR rsp OR scl) AND "
    "authorized_access_point",
    "dc.creator": "contribution.role:("
    "abr OR act OR adi OR adp OR aft OR anm OR ann OR apl OR arr OR ato OR "
    "auc OR aui OR bkd OR bnd OR brd OR brl OR bsl OR cas OR clr OR clt OR "
    "cmm OR cnd OR cng OR cns OR col OR cor OR cou OR cre OR crt OR csl OR "
    "cst OR ctb OR ctg OR ctr OR cur OR cwt OR dfd OR dgg OR dgs OR dnc OR "
    "dnr OR dpt OR drm OR dst OR dte OR dto OR dub OR edm OR edt OR egr OR "
    "etr OR exp OR fac OR fds OR fmd OR fmo OR fmp OR his OR hnr OR hst OR "
    "ill OR ilu OR ins OR isb OR itr OR jud OR jug OR lgd OR ltg OR med OR "
    "mfr OR mod OR msd OR mtk OR mus OR nrt OR orm OR osp OR oth OR own OR "
    "pan OR pat OR pbd OR pbl OR plt OR ppm OR ppt OR pre OR prf OR prm OR "
    "prn OR pro OR prs OR prt OR ptf OR rcd OR rce OR rcp OR rdd OR res OR "
    "rpc OR rsr OR sds OR sgd OR sll OR sng OR spk OR spn OR srv OR stl OR "
    "tch OR tld OR tlp OR trc OR trl OR vac OR vdg OR wac OR wal OR wat OR "
    "win OR wpr OR wst) AND "
    "authorized_access_point",
    "dc.date": 'provisionActivity.type:"bf:Publication" AND provisionActivity.startDate',
    "dc.title": "title.\\*",
    "dc.description": "(summary.label OR note.label OR dissertation.label OR supplementaryContent)",
    "dc.language": "language.value",
    "dc.publisher": 'provisionActivity.type:"bf:Publication" AND '
    'provisionActivity.statement.type:"bf:Agent" AND '
    "provisionActivity.statement.label.value",
    "dc.type": "type.main_type",
    "dc.subtype": "type.subtype",
    "dc.identifier": "identifiedBy.value",
    "dc.relation": "(issuedWith.label OR otherEdition.label OR "
    "otherPhysicalFormat.label OR precededBy.label OR relatedTo.label OR "
    "succeededBy.label OR supplement.label OR supplementTo.label)",
    "dc.coverage": "(temporalCoverage.date OR temporalCoverage.start_date OR "
    "temporalCoverage.end_date OR subjects.entity.authorized_access_point_\\*)",
    "dc.format": "(extent OR dimensions OR bookFormat OR duration OR "
    "contentMediaCarrier.contentType OR contentMediaCarrier.mediaType OR "
    "contentMediaCarrier.carrierType)",
    "dc.rights": "(usageAndAccessPolicy.label OR copyrightDate)",
    "dc.source": "adminMetadata.source",
    "dc.subject": "subjects.entity.authorized_access_point_\\*",
    "dc.organisation": "organisation_pid",
    "dc.library": "library_pid",
    "dc.location": "holdings.location.pid",
    "dc.note": "note.label",
    "dc.tableofcontents": "tableOfContents",
    "dc.abstract": "summary.label",
    "dc.dissertation": "dissertation.label",
}

# End of 'configurable' stuff


def _convert_sort_keys_to_search(sort_keys, query=""):
    """Convert CQL sort keys to search index sort format.

    Transforms a list of CQL sort key Index objects into search index
    sort specifications. Handles sort direction modifiers (/ascending,
    /descending) and missing value handling (/missingLow, /missingHigh).

    Args:
        sort_keys: List of :class:`Index` objects representing sort fields.
            Each Index may have modifiers specifying sort direction.
        query: The original CQL query string, included in any Diagnostic
            raised for unsupported modifiers.

    Returns:
        list: search index sort specifications. Each item is a dict like::

            {"field_name": {"order": "asc", "missing": "_last"}}

        For relevance sorting, returns::

            {"_score": {"order": "desc"}}

    Example::

        # For query: sortBy dc.title/descending dc.date/ascending
        sort_specs = _convert_sort_keys_to_search(query.sort_keys)
        # Returns: [{"title._text.raw": {"order": "desc", ...}}, ...]
    """
    valid_sort_modifiers = {"ascending", "descending", "missinglow", "missinghigh", "missingomit"}
    search_sort = []
    for sort_key in sort_keys:
        # Get the index name
        index_name = str(sort_key).lower()

        # Map to ES sortable field; fall back to prefixed dc. form, then the raw index name
        search_field = (
            SEARCH_SORT_INDEX_MAPPINGS.get(index_name)
            or SEARCH_SORT_INDEX_MAPPINGS.get(f"dc.{sort_key.value}")
            or index_name
        )

        # Default sort order is ascending
        order = "asc"
        missing = "_last"
        missing_pref = None

        # Check modifiers for sort direction and missing value handling
        if hasattr(sort_key, "modifiers") and sort_key.modifiers:
            for modifier in sort_key.modifiers:
                mod_type = str(modifier.type).lower()
                # Remove prefix if present (e.g., cql.descending -> descending)
                if "." in mod_type:
                    mod_type = mod_type.split(".")[-1]
                if mod_type not in valid_sort_modifiers:
                    raise Diagnostic(code=21, message="Unsupported sort modifier", details=mod_type, query=query)
                if mod_type == "descending":
                    order = "desc"
                elif mod_type == "ascending":
                    order = "asc"
                elif mod_type in ("missinglow", "missinghigh", "missingomit"):
                    missing_pref = mod_type

        if missing_pref in _SORT_MISSING_MAP:
            asc_val, desc_val = _SORT_MISSING_MAP[missing_pref]
            missing = asc_val if order == "asc" else desc_val

        # Build the sort specification
        if search_field == "_score":
            # Relevance sorting
            search_sort.append({"_score": {"order": order}})
        else:
            search_sort.append({search_field: {"order": order, "missing": missing}})

    return search_sort


class Diagnostic(Exception):
    """SRU Diagnostic exception for CQL parsing errors.

    Represents an SRU diagnostic message as defined in the SRU standard.
    Can be raised during CQL parsing or query execution to indicate
    errors to the client.

    Common diagnostic codes:
        - 10: Malformed Query (generic)
        - 14: Quoted identifier not allowed
        - 15: Null indexset / Multiple dots in identifier
        - 19: Unsupported relation
        - 21: Unsupported relation/boolean modifiers
        - 25: Reserved operator in unquoted term
        - 26: Badly placed backslash
        - 27: Empty term
        - 32: Only anchoring characters in term
        - 37: Unsupported boolean operator (PROX)
        - 45: Duplicate prefix declaration
        - 80: Sort not supported (deprecated - now supported)

    Attributes:
        code: Numeric diagnostic code from the SRU diagnostic list.
        uri: Base URI for SRU diagnostics.
        message: Human-readable error message.
        details: Additional context about the error.
        query: The original CQL query string that caused the error.
        xml_root: The XML representation of the diagnostic (lazy-initialized).

    See Also:
        SRU Diagnostics: http://www.loc.gov/standards/sru/diagnostics/
    """

    code = 10  # default to generic broken query diagnostic
    uri = "info:srw/diagnostic/1/"
    message = ""
    details = ""
    xml_root = None

    def __str__(self):
        """Return a string representation of the diagnostic.

        Returns:
            A formatted string: "uri/code [message]: details"
        """
        return f"{self.uri}{self.code} [{self.message}]: {self.details}"

    def __init__(self, code=10, message="Malformed Query", details="", query="???"):
        """Initialize a new Diagnostic exception.

        Args:
            code: SRU diagnostic code. Defaults to 10 (Malformed Query).
            message: Human-readable error message.
            details: Additional context or the problematic query fragment.
            query: The original CQL query string.
        """
        self.code = code
        self.message = message
        self.details = details
        self.query = query
        Exception.__init__(self)

    def xml_str(self, pretty_print=True):
        """Xml as string."""
        self.init_xml()
        return etree.tostring(self.xml_root, pretty_print=pretty_print)

    def init_xml(self):
        """Init XML."""
        srw_ns = "http://www.loc.gov/zing/srw/"
        element_srw = ElementMaker(namespace=srw_ns, nsmap={"srw": srw_ns})
        srw_diag_ns = "http://www.loc.gov/zing/srw/diagnostic/"
        element_srw_diag = ElementMaker(namespace=srw_diag_ns, nsmap={"diag": srw_diag_ns})
        self.xml_root = element_srw.searchRetrieveResponse()
        self.xml_root.append(element_srw.version("1.1"))

        echoed_search_rr = element_srw.echoedSearchRetrieveRequest()
        echoed_search_rr.append(element_srw.version("1.1"))
        echoed_search_rr.append(element_srw.query(self.query))
        echoed_search_rr.append(element_srw.recordPacking("xml"))
        self.xml_root.append(echoed_search_rr)
        diagnostics = element_srw.diagnostics()
        diagnostic = element_srw_diag.diagnostic()
        diagnostic.append(element_srw_diag.uri(f"{self.uri}{self.code}"))
        diagnostic.append(element_srw_diag.details(self.details))
        diagnostic.append(element_srw_diag.message(f"{self.message}"))
        diagnostics.append(diagnostic)
        self.xml_root.append(diagnostics)


class PrefixableObject:
    """Base class for CQL objects that carry prefix declarations.

    Provides prefix registration and resolution, climbing the parent tree
    until a match is found or the config is consulted.
    """

    prefixes = {}
    parent = None
    config = None
    error_on_duplicate_prefix = ERROR_ON_DUPLICATE_PREFIX

    def __init__(self, query):
        """Initialise with the raw CQL query string for use in diagnostics.

        :param query: The original CQL query string.
        """
        self.prefixes = {}
        self.parent = None
        self.config = None
        self.query = query

    def add_prefix(self, name, identifier):
        """Register a CQL prefix-to-URI mapping on this object.

        :param name: The prefix name (e.g. ``'dc'``).
        :param identifier: The URI the prefix maps to.
        :raises Diagnostic: code 45 if duplicate prefix detection is enabled
            and the prefix is already declared.
        """
        if self.error_on_duplicate_prefix and (name in self.prefixes or name in RESERVED_PREFIXES):
            raise Diagnostic(code=45, details=name, query=self.query)
        self.prefixes[name] = identifier

    def resolve_prefix(self, name):
        """Resolve a prefix name to its URI by climbing the parent tree.

        Checks reserved prefixes first, then this object's local declarations,
        then delegates upward to the parent, and finally to the config.

        :param name: The prefix name to look up.
        :returns: The URI string for the prefix, or ``None`` if not found.
        """
        # Climb tree
        if name in RESERVED_PREFIXES:
            return RESERVED_PREFIXES[name]
        if name in self.prefixes:
            return self.prefixes[name]
        if self.parent is not None:
            return self.parent.resolve_prefix(name)
        return self.config.resolve_prefix(name) if self.config is not None else None


class PrefixedObject:
    """Base class for CQL objects with an optional namespace prefix.

    Handles the ``prefix.value`` dotted syntax, quoted identifier stripping,
    and validation of multiple dots or a null indexset.
    """

    prefix = ""
    prefix_uri = ""
    value = ""
    parent = None

    def __init__(self, val, query, error_on_quoted_identifier=ERROR_ON_QUOTED_IDENTIFIER):
        """Parse ``val`` into a prefix and local name.

        :param val: Raw token string (e.g. ``'dc.title'`` or ``'title'``).
        :param query: Original CQL query string, used in diagnostics.
        :param error_on_quoted_identifier: Raise diagnostic 14 when ``val`` is
            a quoted string. Defaults to ``ERROR_ON_QUOTED_IDENTIFIER``.
        """
        # All prefixed things are case insensitive
        self.error_on_quoted_identifier = error_on_quoted_identifier
        self.orig_value = val
        self.query = query
        val = val.lower()
        if val and val[0] == '"' and val[-1] == '"':
            if self.error_on_quoted_identifier:
                raise Diagnostic(code=14, details=val, query=self.query)
            val = val[1:-1]
        self.value = val
        self.split_value()

    def __str__(self):
        """String representation of the object."""
        return f"{self.prefix}.{self.value}" if self.prefix else f"{self.value}"

    def split_value(self):
        """Split a dotted value into prefix and local-name components.

        :raises Diagnostic: code 15 on multiple dots or a leading dot (null indexset).
        """
        find_point = self.value.find(".")
        if self.value.count(".") > 1:
            raise Diagnostic(code=15, details=f'Multiple "." characters: {self.value}', query=self.query)
        if find_point == 0:
            raise Diagnostic(code=15, details="Null indexset", query=self.query)
        if find_point >= 0:
            self.prefix = self.value[:find_point].lower()
            self.value = self.value[find_point + 1 :].lower()

    def resolve_prefix(self):
        """Resolve this object's prefix to its full URI.

        Delegates to the parent's ``resolve_prefix`` and caches the result
        in ``prefix_uri``.

        :returns: The URI string for this object's prefix.
        """
        if not self.prefix_uri:
            if isinstance(self.parent, PrefixedObject):
                self.prefix_uri = self.parent.resolve_prefix()
            else:
                self.prefix_uri = self.parent.resolve_prefix(self.prefix)
        return self.prefix_uri


class ModifiableObject:
    """Mixin for CQL objects that accept modifier clauses (e.g. ``/relevant``)."""

    def __init__(self, modifiers=None):
        """Initialise the modifiers list.

        :param modifiers: Pre-parsed list of :class:`ModifierClause` objects,
            or ``None`` to start with an empty list.
        """
        self.modifiers = modifiers or []

    def __getitem__(self, key):
        """Return a modifier by index or by type name.

        :param key: Integer index, or a type-name string to match against.
        :returns: The matching :class:`ModifierClause`, or ``None`` if not found.
        """
        if isinstance(key, int):
            try:
                return self.modifiers[key]
            except IndexError:
                return None
        return next(
            (modifier for modifier in self.modifiers if str(modifier.type) == key or modifier.type.value == key),
            None,
        )


class Triple(PrefixableObject):
    """CQL boolean combination of two operands (left op boolean right)."""

    left_operand = None
    right_operand = None
    boolean = None
    sort_keys = []

    def to_search(self):
        """Create the search representation of the object."""
        boolean = self.boolean.to_search()
        if boolean == "prox":
            raise Diagnostic(code=37, message="Unsupported boolean operator", details="prox", query=self.query)
        left = self.left_operand.to_search()
        right = self.right_operand.to_search()
        # Sort keys are handled separately via get_search_sort()
        if boolean == "not":
            return f"({left} AND NOT {right})"
        return f"({left} {boolean.upper()} {right})"

    def get_search_sort(self):
        """Extract sort keys in search index format.

        Returns a list of sort specifications for search index.
        Each item is either a string (field name) or a dict with options.
        """
        if not self.sort_keys:
            return []
        return _convert_sort_keys_to_search(self.sort_keys, query=self.query)

    def get_result_set_id(self, top=None):
        """Return the result set ID referenced by this query, or an empty string.

        Recursively checks both operands. Returns the ID only when every leaf in
        the tree references the same result set (the CQL 1.2 ``FULL_RESULT_SET_NAME_CHECK``
        rule). Returns ``''`` for NOT/PROX booleans or when no result set is found.

        :param top: Internal recursion sentinel; callers should omit this.
        :returns: The result set ID string, or ``''`` if none is referenced.
        """
        if FULL_RESULT_SET_NAME_CHECK == 0 or self.boolean.value in ("not", "prox"):
            return ""

        is_top_level = top is None
        if is_top_level:
            top = self

        # Iterate over operands and build a list
        rs_list = []
        if isinstance(self.left_operand, Triple):
            rs_list.extend(self.left_operand.get_result_set_id(top))
        else:
            rs_list.append(self.left_operand.get_result_set_id(top))
        if isinstance(self.right_operand, Triple):
            rs_list.extend(self.right_operand.get_result_set_id(top))
        else:
            rs_list.append(self.right_operand.get_result_set_id(top))

        if is_top_level:
            return rs_list[0] if len(rs_list) == rs_list.count(rs_list[0]) else ""
        return rs_list


class SearchClause(PrefixableObject):
    """CQL search clause: a single index/relation/term triplet."""

    index = None
    relation = None
    term = None
    sort_keys = []

    def __init__(self, ind, rel, term, query):
        """Construct a search clause from its parsed components.

        :param ind: The :class:`Index` object.
        :param rel: The :class:`Relation` object.
        :param term: The :class:`Term` object.
        :param query: Original CQL query string, used in diagnostics.
        """
        PrefixableObject.__init__(self, query)
        self.index = ind
        self.relation = rel
        self.term = term
        ind.parent = self
        rel.parent = self
        term.parent = self

    def to_search(self):
        """Create the search representation of the object."""

        def index_term(index, relation, term):
            """Clean term."""
            from .explain import Explain

            # try to map dc mappings
            index = SEARCH_INDEX_MAPPINGS.get(index.lower(), index)
            # try to map search mappings
            index = Explain("tmp").search_mappings.get(index, index)
            if relation in ["=", "all", "any"]:
                relation = ""
            if str(index) == SERVER_CHOICE_INDEX:
                return f"{relation}{term}"
            # Handle multi-field OR expression: "(field1 OR field2)" + term
            # search query string does not support "(f1 OR f2):value"; expand each field.
            if index.startswith("(") and index.endswith(")"):
                fields = [f.strip() for f in index[1:-1].split(" OR ")]
                return f"({' OR '.join(f'{f}:{relation}{term}' for f in fields)})"
            return f"{index}:{relation}{term}"

        index = self.index.to_search()
        relation = self.relation.to_search()
        if relation == "<>":
            search_term = self.term.to_search()
            if not (search_term.startswith('"') and search_term.endswith('"')):
                search_term = f'"{search_term}"'
            text = index_term(index, "-", search_term)
        elif relation in ORDER:
            text = index_term(index, relation, self.term.to_search())
        else:
            texts = []
            for term in self.term.to_search().split(" "):
                texts.append(index_term(index, relation, term))
            if texts:
                texts[0] = texts[0].replace('"', "")
                texts[-1] = texts[-1].rstrip('"')
            if relation == "any":
                text = f"({' OR '.join(texts)})"
            elif relation == "all":
                text = f"({' AND '.join(texts)})"
            else:
                raise Diagnostic(code=19, message="Unsupported relation", details=relation, query=self.query)
        # Sort keys are handled separately via get_search_sort()
        return text

    def get_search_sort(self):
        """Extract sort keys in search index format.

        Returns a list of sort specifications for search index.
        Each item is either a string (field name) or a dict with options.
        """
        if not self.sort_keys:
            return []
        return _convert_sort_keys_to_search(self.sort_keys, query=self.query)

    def get_result_set_id(self, top=None):
        """Return the result set ID if this clause is ``cql.resultSetId = <id>``.

        :param top: Internal recursion sentinel (matches :class:`Triple` interface).
        :returns: The result set ID string, or ``''`` if this clause is not a
            result set reference.
        """
        if self.relation.value not in ("=", "=="):
            return ""
        idx = self.index
        idx.resolve_prefix()
        if idx.prefix_uri in CQL_CONTEXT_SET_URIS and idx.value.lower() == "resultsetid":
            val = self.term.value
            if len(val) >= 2 and val[0] == '"' and val[-1] == '"':
                val = val[1:-1]
            return val
        return ""


def _collect_unsupported_modifiers(modifiers, supported_set):
    """Return a list of unsupported modifier type strings from ``modifiers``.

    Strips any ``prefix.`` component before checking membership. Modifiers in
    ``UNSUPPORTED_RELATION_MODIFIERS`` include an explanatory note in parentheses.

    :param modifiers: Iterable of :class:`ModifierClause` objects to check.
    :param supported_set: Set of lower-case modifier type names that are allowed.
    :returns: List of unsupported modifier description strings (empty if all valid).
    """
    unsupported = []
    for modifier in modifiers:
        mod_type = str(modifier.type).lower()
        if "." in mod_type:
            mod_type = mod_type.rsplit(".", 1)[-1]
        if mod_type not in supported_set:
            if mod_type in UNSUPPORTED_RELATION_MODIFIERS:
                unsupported.append(f"{mod_type} ({UNSUPPORTED_RELATION_MODIFIERS[mod_type]})")
            else:
                unsupported.append(mod_type)
    return unsupported


class Index(PrefixedObject, ModifiableObject):
    """CQL index name, optionally prefixed (e.g. ``dc.title``)."""

    def __init__(self, val, query):
        """Construct an Index, rejecting reserved operator characters.

        :param val: Raw index token string.
        :param query: Original CQL query string, used in diagnostics.
        :raises Diagnostic: code 10 when ``val`` is a parenthesis or relation operator.
        """
        ModifiableObject.__init__(self)
        PrefixedObject.__init__(self, val, query)
        if self.value in ("(", ")", *ORDER):
            raise Diagnostic(message="Invalid characters in index name", details=self.value, query=self.query)

    def to_search(self):
        """Create the search representation of the object."""
        if self.modifiers:
            # Sort modifiers are handled by get_search_sort(); check remaining ones.
            supported = SEARCH_SORT_MODIFIERS.keys() | SUPPORTED_RELATION_MODIFIERS.keys()
            if unsupported := _collect_unsupported_modifiers(self.modifiers, supported):
                raise Diagnostic(
                    code=21, message="Unsupported index modifier(s)", details=", ".join(unsupported), query=self.query
                )
        return str(self)


class Relation(PrefixedObject, ModifiableObject):
    """CQL relation operator (``=``, ``any``, ``all``, ``<``, etc.) with optional modifiers."""

    def __init__(self, rel, query, mods=None):
        """Construct a Relation with optional modifiers.

        :param rel: Raw relation token (e.g. ``'='``, ``'any'``).
        :param query: Original CQL query string, used in diagnostics.
        :param mods: Pre-parsed list of :class:`ModifierClause` objects.
        """
        self.prefix = "cql"
        ModifiableObject.__init__(self, mods)
        PrefixedObject.__init__(self, rel, query)
        for mod in self.modifiers:
            mod.parent = self

    def to_search(self):
        """Create the search representation of the object."""
        if self.modifiers:
            if unsupported := _collect_unsupported_modifiers(self.modifiers, SUPPORTED_RELATION_MODIFIERS):
                raise Diagnostic(
                    code=21,
                    message="Unsupported relation modifier(s)",
                    details=", ".join(unsupported),
                    query=self.query,
                )
            # Supported modifiers are acknowledged but don't change the ES query
            # (ES handles relevance, word matching, and case insensitivity by default)
        return self.value


class Term:
    """CQL search term, validated at construction time."""

    value = ""

    def __init__(self, value, query, error_on_empty_term=ERROR_ON_EMPTY_TERM):
        """Construct and validate a CQL search term.

        Raises diagnostics for reserved operator tokens, anchoring-only terms,
        badly placed backslashes, and (optionally) empty terms.

        :param value: Raw term string from the lexer.
        :param query: Original CQL query string, used in diagnostics.
        :param error_on_empty_term: Raise diagnostic 27 for empty terms.
            Defaults to ``ERROR_ON_EMPTY_TERM``.
        :raises Diagnostic: codes 25, 26, 27, or 32 for invalid term content.
        """
        if value != "":
            # Unquoted literal
            if value in (">=", "<=", ">", "<", "<>", "/", "="):
                raise Diagnostic(code=25, details=value, query=query)

            if not any(char != "^" for char in value):
                raise Diagnostic(code=32, details=f"Only anchoring character(s) in term: {value}", query=query)

            # Unescape quotes
            # if (value[0] == '"' and value[-1] == '"'):
            #     value = value[1:-1]
            # value = value.replace('\\"', '"')

            # Check for badly placed backslashes
            idx = 0
            while True:
                idx = value.find("\\", idx)
                if idx == -1:
                    break
                if idx + 1 >= len(value) or value[idx + 1] not in ("?", "\\", "*", "^"):
                    raise Diagnostic(code=26, details=value, query=query)
                idx += 2 if value[idx + 1] == "\\" else 1
        elif error_on_empty_term:
            raise Diagnostic(code=27, query=query)
        self.value = value

    def __str__(self):
        """String representation of the object."""
        return f"{self.value}"

    def to_search(self):
        """Create the search representation of the object."""
        return self.value


class Boolean(ModifiableObject):
    """CQL boolean operator (``and``, ``or``, ``not``, ``prox``) with optional modifiers."""

    value = ""
    parent = None

    def __init__(self, bool_value, query, mods=None):
        """Construct a Boolean operator with optional modifiers.

        :param bool_value: Boolean keyword (``'and'``, ``'or'``, ``'not'``, ``'prox'``).
        :param query: Original CQL query string, used in diagnostics.
        :param mods: Pre-parsed list of :class:`ModifierClause` objects.
        """
        ModifiableObject.__init__(self, mods)
        self.value = bool_value
        self.parent = None
        self.query = query

    def to_search(self):
        """Create the search representation of the object."""
        if self.modifiers:
            raise Diagnostic(
                code=21,
                message="Unsupported boolean modifier(s)",
                details=", ".join(str(m.type) for m in self.modifiers),
                query=self.query,
            )
        return f"{self.value}"

    def resolve_prefix(self, name):
        """Resolve a prefix by delegating to the parent :class:`Triple`."""
        return self.parent.resolve_prefix(name)


class ModifierTypeType(PrefixedObject):
    """CQL modifier type name, parsed as a prefixed object."""

    # Same as index, but we'll XCQLify in ModifierClause
    parent = None
    prefix = "cql"


class ModifierClause:
    """A single slash-separated CQL modifier (e.g. ``/relevant`` or ``/sort.ascending``)."""

    parent = None
    type = None
    comparison = ""
    value = ""

    def __init__(self, modifier_type, comp="", val="", query=""):
        """Construct a modifier clause.

        :param modifier_type: The modifier type string (e.g. ``'relevant'``, ``'descending'``).
        :param comp: Optional comparison operator (``'='``, ``'<'``, etc.).
        :param val: Optional modifier value.
        :param query: Original CQL query string, used in diagnostics.
        """
        self.type = ModifierType(modifier_type, query)
        self.type.parent = self
        self.comparison = comp
        self.value = val

    def __str__(self):
        """String representation of the object."""
        if self.value:
            return f"{self.type}{self.comparison}{self.value}"
        return f"{self.type}"

    def to_search(self):
        """Return self; modifier clauses are consumed directly by their parent objects."""
        return self

    def resolve_prefix(self, name):
        """Resolve a prefix by skipping the immediate parent (boolean/relation) and delegating up."""
        # Need to skip parent, which has its own resolve_prefix
        # eg boolean or relation, neither of which is prefixable
        return self.parent.parent.resolve_prefix(name)


# Requires changes for:  <= >= <>, and escaped \" in "
# From shlex.py (std library for 2.2+)
class CQLshlex(shlex):
    """Shlex with additions for CQL parsing."""

    quotes = '"'
    commenters = ""
    next_token = ""

    def __init__(self, thing, query):
        """Set up the CQL lexer with extended word characters for CQL syntax.

        :param thing: File-like object to read tokens from.
        :param query: Original CQL query string, stored for use in diagnostics.
        """
        shlex.__init__(self, thing)
        self.wordchars += "!@#$%^&*-+{}[];,.?|~`:\\"
        self.query = query

    def read_token(self):
        """Read a token from the input stream (no pushback or inclusions)."""
        while True:
            if self.next_token:
                self.token = self.next_token
                self.next_token = ""
                if self.token == "/":
                    self.state = " "
                    break

            nextchar = self.instream.read(1)
            if nextchar == "\n":
                self.lineno += 1

            if self.state is None:
                self.token = ""  # past end of file
                break
            if self.state == " ":
                done = self._read_token_space(nextchar)
            elif self.state == "<":
                done = self._read_token_angle(nextchar)
            elif self.state in self.quotes:
                done = self._read_token_quote(nextchar)
            elif self.state == "a":
                done = self._read_token_word(nextchar)
            else:
                done = False
            if done:
                break

        result = self.token
        self.token = ""
        return result

    def _read_token_space(self, nextchar):
        """Handle space state: scanning between tokens.

        :param nextchar: The next character read from the input stream.
        :returns: True if a token boundary was reached, False otherwise.
        :rtype: bool
        """
        if not nextchar:
            self.state = None
            return True
        if nextchar in self.whitespace:
            return bool(self.token)
        if nextchar in self.commenters:
            self.instream.readline()
            self.lineno += 1
        elif nextchar in self.wordchars:
            self.token = nextchar
            self.state = "a"
        elif nextchar in self.quotes:
            self.token = nextchar
            self.state = nextchar
        elif nextchar in ["<", ">"]:
            self.token = nextchar
            self.state = "<"
        else:
            self.token = nextchar
            return bool(self.token)
        return False

    def _read_token_angle(self, nextchar):
        """Handle angle-bracket state: accumulating <=, >= or <>.

        :param nextchar: The next character read from the input stream.
        :returns: Always True — any character ends this state.
        :rtype: bool
        """
        if self.token == ">" and nextchar == "=":
            self.token += nextchar
            self.state = " "
            return True
        if self.token == "<" and nextchar in [">", "="]:
            self.token += nextchar
            self.state = " "
            return True
        if not nextchar:
            self.state = None
            return True
        if nextchar == "/":
            self.state = "/"
            self.next_token = "/"
            return True
        if nextchar in self.wordchars:
            self.state = "a"
            self.next_token = nextchar
            return True
        if nextchar in self.quotes:
            self.state = nextchar
            self.next_token = nextchar
            return True
        self.state = " "
        return True

    def _read_token_quote(self, nextchar):
        """Handle quoted-string state: accumulating until the closing quote.

        :param nextchar: The next character read from the input stream.
        :returns: True if the closing quote was found, False otherwise.
        :rtype: bool
        :raises Diagnostic: If end of file is reached inside a quoted string.
        """
        self.token += nextchar
        if nextchar == self.state and self.token[-2] != "\\":
            self.state = " "
            return True
        if not nextchar:
            raise Diagnostic(details=self.token[:-1], query=self.query)
        return False

    def _read_token_word(self, nextchar):
        """Handle word state: accumulating an unquoted token.

        :param nextchar: The next character read from the input stream.
        :returns: True if a token boundary was reached, False otherwise.
        :rtype: bool
        """
        if not nextchar:
            self.state = None
            return True
        if nextchar in self.whitespace:
            self.state = " "
            return bool(self.token)
        if nextchar in self.commenters:
            self.instream.readline()
            self.lineno += 1
        elif ord(nextchar) > 126 or nextchar in self.wordchars or nextchar in self.quotes:
            self.token += nextchar
        elif nextchar in [">", "<"]:
            self.next_token = nextchar
            self.state = "<"
            return True
        else:
            self.push_token(nextchar)
            self.state = " "
            return bool(self.token)
        return False


class CQLParser:
    """Token parser to create object structure for CQL."""

    parser = ""
    current_token = ""
    next_token = ""

    def __init__(self, parser):
        """Initialise with shlex parser."""
        self.parser = parser
        self.fetch_token()  # Fetches to next
        self.fetch_token()  # Fetches to curr

    @staticmethod
    def is_sort(token):
        """Return ``True`` if ``token`` is the ``sortBy`` keyword."""
        return token.lower() == SORT_WORD

    @staticmethod
    def is_boolean(token):
        """Return ``True`` if ``token`` is a CQL boolean keyword."""
        token = token.lower()
        return token in BOOLEANS

    def fetch_token(self):
        """Read ahead one token."""
        self.current_token = self.next_token
        self.next_token = self.parser.get_token()

    def prefixes(self):
        """Parse all ``>prefix=uri`` declarations at the current position.

        :returns: Dict mapping prefix names to URI strings.
        """
        prefs = {}
        while self.current_token == ">":
            # Strip off maps
            self.fetch_token()
            if self.next_token == "=":
                # Named map
                name = self.current_token
                self.fetch_token()  # = is current
                self.fetch_token()  # id is current
            else:
                name = ""
            identifier = [self.current_token]
            self.fetch_token()
            # URIs can have slashes, and may be unquoted (standard BNF checked)
            while self.current_token == "/" or identifier[-1] == "/":
                identifier.append(self.current_token)
                self.fetch_token()
            identifier = "".join(identifier)
            if len(identifier) > 1 and identifier[0] == '"' and identifier[-1] == '"':
                identifier = identifier[1:-1]
            prefs[name.lower()] = identifier
        return prefs

    def query(self):
        """Parse a complete CQL query and return a :class:`Triple` or :class:`SearchClause`.

        Handles prefix declarations, boolean combinations, and ``sortBy`` clauses.

        :returns: The parsed query root object.
        """
        prefs = self.prefixes()
        left = self.sub_query()
        while self.current_token:
            if self.is_boolean(self.current_token):
                boolobject = self.boolean()
                right = self.sub_query()
                trip = TripleType(self.parser.query)
                # Setup objects
                trip.left_operand = left
                trip.boolean = boolobject
                trip.right_operand = right
                left.parent = trip
                right.parent = trip
                boolobject.parent = trip
                left = trip
            elif self.is_sort(self.current_token):
                # consume and parse with modified sort spec
                left.sort_keys = self.sort_query()
            else:
                break
        for key, value in prefs.items():
            left.add_prefix(key, value)
        return left

    def sort_query(self):
        """Parse sort key specifications following the ``sortBy`` keyword.

        :returns: List of :class:`Index` objects representing the sort keys.
        :raises Diagnostic: code 10 when no sort keys follow ``sortBy``.
        """
        # current is 'sort' reserved word
        self.fetch_token()
        keys = []
        if not self.current_token:
            raise Diagnostic(message="No sort keys supplied", query=self.parser.query)
        while self.current_token and self.current_token != ")":
            index = IndexerType(self.current_token, self.parser.query)
            self.fetch_token()
            index.modifiers = self.modifiers()
            keys.append(index)
        return keys

    def sub_query(self):
        """Parse a parenthesised sub-query, a prefix block, or a plain search clause.

        :returns: Parsed :class:`Triple` or :class:`SearchClause`.
        """
        if self.current_token == "(":
            self.fetch_token()  # Skip (
            query = self.query()
            if self.current_token == ")":
                self.fetch_token()  # Skip )
            else:
                raise Diagnostic(details=self.current_token, query=self.parser.query)
        elif prefs := self.prefixes():
            query = self.query()
            for key, value in prefs.items():
                query.add_prefix(key, value)
        else:
            query = self.clause()
        return query

    def clause(self):
        """Parse a search clause (index, relation, and term) or a server-choice clause.

        :returns: A :class:`SearchClause` object.
        """
        is_boolean = self.is_boolean(self.next_token)
        sort = self.is_sort(self.next_token)
        if not sort and not is_boolean and self.next_token not in [")", "(", ""]:
            irt = self._parse_index_clause()
        elif self.current_token and (is_boolean or sort or self.next_token in [")", ""]):
            irt = SearchClauseType(
                IndexerType(SERVER_CHOICE_INDEX, self.parser.query),
                RelationType(SERVER_CHOICE_RELATION, self.parser.query),
                TermType(self.current_token, self.parser.query),
                self.parser.query,
            )
            self.fetch_token()

        elif self.current_token == ">":
            prefs = self.prefixes()
            clause = self.clause()
            for key, value in prefs.items():
                clause.add_prefix(key, value)
            return clause

        else:
            raise Diagnostic(
                details=f"Expected Boolean or Relation but got: {self.current_token}",
                query=self.parser.query,
            )
        return irt

    def _parse_index_clause(self):
        index = IndexerType(self.current_token, self.parser.query)
        self.fetch_token()  # Skip Index
        relation = self.relation()
        if self.current_token == "":
            raise Diagnostic(details="Expected Term, got end of query.", query=self.parser.query)
        term = TermType(self.current_token, self.parser.query)
        self.fetch_token()  # Skip Term
        return SearchClauseType(index, relation, term, self.parser.query)

    def modifiers(self):
        """Parse zero or more slash-separated modifier clauses at the current position.

        :returns: List of :class:`ModifierClause` objects.
        """
        mods = []
        while self.current_token == MODIFIER_SEPARATOR:
            self.fetch_token()
            mod = self.current_token
            mod = mod.lower()
            if mod == MODIFIER_SEPARATOR:
                raise Diagnostic(details="Null modifier", query=self.parser.query)
            self.fetch_token()
            comp = self.current_token
            if comp in ORDER:
                self.fetch_token()
                value = self.current_token
                self.fetch_token()
            else:
                comp = ""
                value = ""
            mods.append(ModifierClause(mod, comp, value, self.parser.query))
        return mods

    def boolean(self):
        """Parse a boolean operator and any attached modifiers.

        :returns: A :class:`Boolean` object.
        :raises Diagnostic: code 10 if the current token is not a valid boolean.
        """
        self.current_token = self.current_token.lower()
        if self.current_token not in BOOLEANS:
            raise Diagnostic(details=self.current_token, query=self.parser.query)
        bool_type = BooleanType(self.current_token, self.parser.query)
        self.fetch_token()
        bool_type.modifiers = self.modifiers()
        for modifier in bool_type.modifiers:
            modifier.parent = bool_type
        return bool_type

    def relation(self):
        """Parse a relation operator and any attached modifiers.

        :returns: A :class:`Relation` object.
        """
        self.current_token = self.current_token.lower()
        relation = RelationType(self.current_token, self.parser.query)
        self.fetch_token()
        relation.modifiers = self.modifiers()
        for modifier in relation.modifiers:
            modifier.parent = relation
        return relation


def parse(query):
    """Parse a CQL query string and return a :class:`Triple` or :class:`SearchClause`.

    :param query: CQL query string to parse.
    :returns: Parsed :class:`Triple` or :class:`SearchClause` object.
    :raises Diagnostic: on any parse error.
    """
    query = strip_chars(query)
    lexer = CQLshlex(StringIO(query), query)
    parser = CQLParser(lexer)
    result = parser.query()
    if parser.current_token != "":
        raise Diagnostic(code=10, details=f"Unprocessed tokens remain: {parser.current_token!r}", query=query)
    return result


# Assign our objects to generate
TripleType = Triple
BooleanType = Boolean
RelationType = Relation
SearchClauseType = SearchClause
ModifierClauseType = ModifierClause
ModifierType = ModifierTypeType
IndexerType = Index
TermType = Term
