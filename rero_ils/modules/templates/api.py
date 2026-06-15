# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""API for manipulating Templates."""

from functools import partial

from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import extracted_data_from_ref

from .extensions import CleanDataDictExtension
from .models import TemplateIdentifier, TemplateMetadata, TemplateVisibility

# provider
TemplateProvider = type(
    "TemplateProvider",
    (Provider,),
    {"identifier": TemplateIdentifier, "pid_type": "tmpl"},
)
# minter
template_id_minter = partial(id_minter, provider=TemplateProvider)
# fetcher
template_id_fetcher = partial(id_fetcher, provider=TemplateProvider)


class TemplatesSearch(IlsRecordsSearch):
    """RecordsSearch for Templates."""

    class Meta:
        """Search only on Templates index."""

        index = "templates"
        doc_types = None
        fields = ("*",)
        facets = {}

        default_filter = None


class Template(IlsRecord):
    """Templates class."""

    _extensions = [CleanDataDictExtension()]

    minter = template_id_minter
    fetcher = template_id_fetcher
    provider = TemplateProvider
    model_cls = TemplateMetadata
    schema = "templates/template-v0.0.1.json"
    pids_exist_check = {"required": {"org": "organisation", "ptrn": "creator"}}

    def replace_refs(self):
        """Replace the ``$ref`` keys within the JSON."""
        # For template, we don't need to resolve $ref inside the ``data``
        # attribute. Other $ref should be resolved.
        data = self.pop("data", {})
        dumped = super().replace_refs()
        dumped["data"] = data
        self["data"] = data
        return dumped

    @property
    def creator_pid(self):
        """Shortcut for template creator pid."""
        if self.get("creator"):
            return extracted_data_from_ref(self.get("creator"))
        return None

    @property
    def is_public(self):
        """Shortcut for template public visibility."""
        return self.get("visibility") == TemplateVisibility.PUBLIC

    @property
    def is_private(self):
        """Shortcut for template private visibility."""
        return self.get("visibility") == TemplateVisibility.PRIVATE


class TemplatesIndexer(IlsRecordsIndexer):
    """Indexing templates in search index."""

    record_cls = Template

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type="tmpl")
