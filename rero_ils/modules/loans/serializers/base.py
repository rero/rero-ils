# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""RERO-ILS Loan resource serializers shared helpers."""

import ciso8601
from flask import current_app, request
from invenio_i18n.ext import current_i18n

from rero_ils.modules.documents.api import DocumentsSearch
from rero_ils.modules.documents.extensions import TitleExtension
from rero_ils.modules.holdings.api import HoldingsSearch
from rero_ils.utils import get_i18n_supported_languages

from ..api import Loan


def _display_language():
    """Get the language used to display the localized entity names."""
    language = request.args.get("lang", current_i18n.language)
    if not language or language not in get_i18n_supported_languages():
        language = current_app.config.get("BABEL_DEFAULT_LANGUAGE", "en")
    return language


def _document_contributions(document, language):
    """Get the first contributions of a document as a single string.

    :param document: the document data from the search index.
    :param language: the language used for the authorized access points.
    """
    names = []
    for contribution in document.get("contribution", [])[:3]:
        entity = contribution.get("entity", {})
        if name := entity.get(f"authorized_access_point_{language}") or entity.get("authorized_access_point"):
            names.append(name)
    return " ; ".join(names)


def _item_location(item):
    """Format the owning library and location of an item.

    The temporary location takes precedence, as in the professional interface.

    :param item: the item data from the search index.
    """
    name = item.get("temporary_location", {}).get("name") or item.get("location", {}).get("name", "")
    return f"{item.get('library', {}).get('name', '')} - {name}"


def _pickup_location(loan):
    """Format the pickup location of a loan.

    The location pickup name takes precedence, as in the professional interface.

    :param loan: the loan data from the search index.
    """
    location = loan.get("pickup_location", {})
    if pickup_name := location.get("pickup_name"):
        return pickup_name
    return f"{location.get('library_name', '')}: {location.get('name', '')}"


def requests_to_validate_rows(library):
    """Get the requests to validate of a library as flat export rows.

    The requests are the same as the ones listed by the professional interface.
    Only the documents and the call numbers inherited from the holdings need to
    be loaded, both with a single search each.

    :param library: the `Library` record to export the requests from.
    :returns: a list of dict, one per request.
    """
    metadata = Loan.requested_loans_to_validate(library.pid)
    language = _display_language()
    timezone = library.get_timezone()
    documents = DocumentsSearch().get_records_by_terms(
        [data["loan"]["document_pid"] for data in metadata],
        fields=["pid", "title", "contribution"],
        as_dict=True,
    )
    holdings = HoldingsSearch().get_records_by_terms(
        [data["item"]["holding"]["pid"] for data in metadata],
        fields=["pid", "call_number", "second_call_number"],
        as_dict=True,
    )

    rows = []
    for data in metadata:
        item, loan = data["item"], data["loan"]
        document = documents.get(loan["document_pid"], {})
        holding = holdings.get(item["holding"]["pid"], {})
        request_date = ciso8601.parse_datetime(loan["creation_date"]).astimezone(timezone)
        rows.append(
            {
                "item_barcode": item.get("barcode", ""),
                "document_title": TitleExtension.format_text(document.get("title", [])),
                "document_contributions": _document_contributions(document, language),
                "item_first_call_number": item.get("call_number") or holding.get("call_number", ""),
                "item_second_call_number": item.get("second_call_number") or holding.get("second_call_number", ""),
                "item_enumerationAndChronology": item.get("enumerationAndChronology", ""),
                "requested_by": f"{loan['patron']['name']} ({loan['patron']['barcode']})",
                "item_location": _item_location(item),
                "pickup_location": _pickup_location(loan),
                "request_date": request_date.strftime("%Y-%m-%d %H:%M"),
            }
        )
    return rows
