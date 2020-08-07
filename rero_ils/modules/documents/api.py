# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLouvain
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

"""API for manipulating documents."""


from functools import partial

from flask import current_app
from invenio_circulation.search.api import search_by_pid
from invenio_search.api import RecordsSearch

from .models import DocumentIdentifier, DocumentMetadata
from .utils import edition_format_text, publication_statement_text, \
    series_statement_format_text, title_format_text_head
from ..acq_order_lines.api import AcqOrderLinesSearch
from ..api import IlsRecord, IlsRecordsIndexer
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..organisations.api import Organisation
from ..providers import Provider

# provider
DocumentProvider = type(
    'DocumentProvider',
    (Provider,),
    dict(identifier=DocumentIdentifier, pid_type='doc')
)
# minter
document_id_minter = partial(id_minter, provider=DocumentProvider)
# fetcher
document_id_fetcher = partial(id_fetcher, provider=DocumentProvider)


class DocumentsSearch(RecordsSearch):
    """DocumentsSearch."""

    class Meta:
        """Search only on documents index."""

        index = 'documents'
        doc_types = None


def search_document_by_pid(pid):
    """Retrieve document by pid from index."""
    query = DocumentsSearch().filter('term', pid=pid)
    try:
        return next(query.scan())
    except StopIteration:
        return None


class Document(IlsRecord):
    """Document class."""

    minter = document_id_minter
    fetcher = document_id_fetcher
    provider = DocumentProvider
    model_cls = DocumentMetadata

    def is_available(self, view_code):
        """Get availability for document."""
        from ..holdings.api import Holding
        if view_code != current_app.config.get(
                'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
            view_id = Organisation.get_record_by_viewcode(view_code)['pid']
            for holding_pid in Holding.get_holdings_pid_by_document_pid_by_org(
                    self.pid, view_id):
                holding = Holding.get_record_by_pid(holding_pid)
                if holding.available:
                    return True
        else:
            for holding_pid in Holding.get_holdings_pid_by_document_pid(
                    self.pid):
                holding = Holding.get_record_by_pid(holding_pid)
                if holding.available:
                    return True
        return False

    @property
    def harvested(self):
        """Is this record harvested from an external service."""
        return self.get('harvested', False)

    @property
    def can_edit(self):
        """Return a boolean for can_edit resource."""
        # TODO: Make this condition on data
        return not self.harvested

    def get_number_of_items(self):
        """Get number of items for document."""
        from ..items.api import ItemsSearch
        return ItemsSearch().filter(
            'term', document__pid=self.pid).count()

    def get_number_of_holdings(self):
        """Get number of holdings for document."""
        from ..holdings.api import HoldingsSearch
        return HoldingsSearch().filter(
            'term', document__pid=self.pid).count()

    def get_number_of_loans(self):
        """Get number of document loans."""
        from ..loans.api import LoanState
        search = search_by_pid(
            document_pid=self.pid,
            exclude_states=[
                LoanState.CANCELLED,
                LoanState.ITEM_RETURNED,
            ]
        )
        return search.source().count()

    def get_number_of_acquisition_order_lines(self):
        """Get number of acquisition order lines for document."""
        return AcqOrderLinesSearch().filter(
            'term', document__pid=self.pid).count()

    def get_links_to_me(self):
        """Get number of links."""
        links = {}
        # get number of document holdings
        number_of_holdings = self.get_number_of_holdings()
        if number_of_holdings:
            links['holdings'] = number_of_holdings
        # get number of items linked
        number_of_items = self.get_number_of_items()
        if number_of_items:
            links['items'] = number_of_items
        # get number of loans linked
        number_of_loans = self.get_number_of_loans()
        if number_of_loans:
            links['loans'] = number_of_loans
        # get number of acquisition order lines linked
        number_of_order_lines = self.get_number_of_acquisition_order_lines()
        if number_of_order_lines:
            links['acq_order_lines'] = number_of_order_lines
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        if links:
            cannot_delete['links'] = links
        if self.harvested:
            cannot_delete['others'] = dict(harvested=True)
        return cannot_delete

    @classmethod
    def post_process(cls, dump):
        """Post process data after a dump.

        :param dump: a dictionary of a resulting Record dumps
        "return: a modified dictionary
        """
        provision_activities = dump.get('provisionActivity', [])
        for provision_activity in provision_activities:
            pub_state_text = publication_statement_text(provision_activity)
            if pub_state_text:
                provision_activity['_text'] = pub_state_text
        series = dump.get('seriesStatement', [])
        for series_element in series:
            series_element["_text"] = series_statement_format_text(
                series_element
            )
        editions = dump.get('editionStatement', [])
        for edition in editions:
            edition['_text'] = edition_format_text(edition)
        titles = dump.get('title', [])
        bf_titles = list(filter(lambda t: t['type'] == 'bf:Title', titles))
        for title in bf_titles:
            title['_text'] = title_format_text_head(titles, with_subtitle=True)
        return dump

    def dumps(self, **kwargs):
        """Return pure Python dictionary with record metadata."""
        return self.post_process(super(Document, self).dumps(**kwargs))

    def index_persons(self, bulk=False):
        """Index all attached persons."""
        from ..persons.api import Person
        persons_ids = []
        for author in self.get('authors', []):
            person = None
            ref = author.get('$ref')
            if ref:
                person = Person.get_record_by_ref(ref)
            pid = author.get('pid')
            if pid:
                person = Person.get_record_by_pid(pid)
            if person:
                if bulk:
                    persons_ids.append(person.id)
                else:
                    person.reindex()
        if persons_ids:
            IlsRecordsIndexer().bulk_index(persons_ids, doc_type=['pers'])

    @classmethod
    def get_all_serial_pids(cls):
        """Get pids of all serial documents.

        a serial document has mode_of_issuance main_type equal to rdami:1003
        """
        es_documents = DocumentsSearch()\
            .filter('term', issuance__main_type="rdami:1003")\
            .source(['pid']).scan()
        for es_document in es_documents:
            yield es_document.pid

    @classmethod
    def get_document_pids_by_issn(cls, issn_number):
        """Get pids of documents having the given issn.

        :param issn_number: the ISSN number
        :param issn_number: str
        :return: the pids of the record having the given ISSN
        :rtype: generator
        """
        es_documents = DocumentsSearch()\
            .filter('term', identifiedBy__type="bf:Issn")\
            .filter('term', identifiedBy__value=issn_number)\
            .source(['pid']).scan()
        for es_document in es_documents:
            yield es_document.pid

    def replace_refs(self):
        """Replace $ref with real data."""
        from ..persons.api import Person
        authors = self.get('authors', [])
        for idx, author in enumerate(authors):
            ref = author.get('$ref')
            if ref:
                person = Person.get_record_by_ref(ref)
                if person:
                    authors[idx] = person
        return super(Document, self).replace_refs()


class DocumentsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = Document

    def index(self, record):
        """Index an document."""
        return_value = super(DocumentsIndexer, self).index(record)
        record.index_persons()
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(DocumentsIndexer, self).bulk_index(record_id_iterator,
                                                 doc_type='doc')
