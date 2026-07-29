# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Inventory list REST API."""

from functools import partial

from invenio_rest import ContentNegotiatedMethodView

from rero_ils.modules.decorators import check_logged_as_librarian
from rero_ils.modules.items.api import ItemsSearch
from rero_ils.modules.items.serializers import csv_item_search, excel_xml_item_search
from rero_ils.query import items_search_factory


class InventoryListResource(ContentNegotiatedMethodView):
    """Inventory List REST resource."""

    # TODO: is candidate for invenio-record-resource ?

    def __init__(self, **kwargs):
        """Init."""
        super().__init__(
            method_serializers={
                "GET": {
                    "application/vnd.ms-excel": excel_xml_item_search,
                    "text/csv": csv_item_search,
                }
            },
            serializers_query_aliases={
                "csv": "text/csv",
                "xml": "application/vnd.ms-excel",
            },
            default_method_media_type={"GET": "text/csv"},
            default_media_type="text/csv",
            **kwargs,
        )
        self.search_factory = partial(items_search_factory, self)

    @check_logged_as_librarian
    def get(self, **kwargs):
        """Search records."""
        search_obj = ItemsSearch()
        search, qs_kwargs = self.search_factory(search_obj)

        return self.make_response(pid_fetcher=None, search_result=search.scan())
