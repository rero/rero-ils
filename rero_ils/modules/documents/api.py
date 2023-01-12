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


from copy import deepcopy
from functools import partial

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Q
from flask import current_app
from invenio_circulation.search.api import search_by_pid
from invenio_records.api import _records_state
from invenio_search import current_search_client
from jsonschema.exceptions import ValidationError

from rero_ils.modules.acquisition.acq_order_lines.api import \
    AcqOrderLinesSearch
from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.commons.identifiers import IdentifierFactory, \
    IdentifierType
from rero_ils.modules.documents.extensions import AddMEFPidExtension
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.minters import id_minter
from rero_ils.modules.operation_logs.extensions import \
    OperationLogObserverExtension
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import sorted_pids

from .models import DocumentIdentifier, DocumentMetadata, DocumentSubjectType
from .utils import edition_format_text, publication_statement_text, \
    series_statement_format_text, title_format_text_head

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


class DocumentsSearch(IlsRecordsSearch):
    """DocumentsSearch."""

    class Meta:
        """Search only on documents index."""

        index = 'documents'
        doc_types = None
        fields = ('*', )
        facets = {}

        default_filter = None


class Document(IlsRecord):
    """Document class."""

    minter = document_id_minter
    fetcher = document_id_fetcher
    provider = DocumentProvider
    model_cls = DocumentMetadata

    _extensions = [
        OperationLogObserverExtension(),
        AddMEFPidExtension()
    ]

    def _validate(self, **kwargs):
        """Validate record against schema and $ref pids."""
        json = super()._validate(**kwargs)

        if self.pid_check:
            from ..utils import pids_exists_in_data
            validation_message = pids_exists_in_data(
                info=f'{self.provider.pid_type} ({self.pid})',
                data=self,
                required={},
                not_required={'doc': [
                    'supplement', 'supplementTo', 'otherEdition',
                    'otherPhysicalFormat', 'issuedWith', 'precededBy',
                    'succeededBy', 'relatedTo', 'hasReproduction',
                    'reproductionOf'
                ]}
            ) or True
            if validation_message is True:
                # also test partOf
                part_of = self.get('partOf', [])
                if part_of:
                    # make a list of refs for easier testing
                    part_of_documents = [doc['document'] for doc in part_of]
                    validation_message = pids_exists_in_data(
                        info=f'{self.provider.pid_type} ({self.pid})',
                        data={'partOf': part_of_documents},
                        required={},
                        not_required={'doc': 'partOf'}
                    ) or True
            if validation_message is not True:
                raise ValidationError(';'.join(validation_message))
        return json

    @classmethod
    def is_available(cls, pid, view_code, raise_exception=False):
        """Get availability for document."""
        from ..holdings.api import Holding
        holding_pids = []
        if view_code != current_app.config.get(
                'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
            view_id = Organisation.get_record_by_viewcode(view_code)['pid']
            holding_pids = Holding.get_holdings_pid_by_document_pid_by_org(
                    pid, view_id)
        else:
            holding_pids = Holding.get_holdings_pid_by_document_pid(pid)
        for holding_pid in holding_pids:
            if holding := Holding.get_record_by_pid(holding_pid):
                if holding.available:
                    return True
            else:
                msg = f'No holding: {holding_pid} in DB ' \
                      f'for document: {pid}'
                current_app.logger.error(msg)
                if raise_exception:
                    raise ValueError(msg)
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

    def get_links_to_me(self, get_pids=False):
        """Record links.

        :param get_pids: if True list of linked pids
                         if False count of linked records
        """
        links = {}
        from ..holdings.api import HoldingsSearch
        from ..items.api import ItemsSearch
        from ..loans.models import LoanState
        hold_query = HoldingsSearch().filter('term', document__pid=self.pid)
        item_query = ItemsSearch().filter('term', document__pid=self.pid)
        loan_query = search_by_pid(
            document_pid=self.pid,
            exclude_states=[LoanState.CANCELLED, LoanState.ITEM_RETURNED]
        )
        acq_order_lines_query = AcqOrderLinesSearch() \
            .filter('term', document__pid=self.pid)
        relation_types = {
            'partOf': 'partOf.document.pid',
            'supplement': 'supplement.pid',
            'supplementTo': 'supplementTo.pid',
            'otherEdition': 'otherEdition.pid',
            'otherPhysicalFormat': 'otherPhysicalFormat.pid',
            'issuedWith': 'issuedWith.pid',
            'precededBy': 'precededBy.pid',
            'succeededBy': 'succeededBy.pid',
            'relatedTo': 'relatedTo.pid',
            'hasReproduction': 'hasReproduction.pid',
            'reproductionOf': 'reproductionOf.pid'
        }

        if get_pids:
            holdings = sorted_pids(hold_query)
            items = sorted_pids(item_query)
            loans = sorted_pids(loan_query)
            acq_order_lines = sorted_pids(acq_order_lines_query)
            documents = {}
            for relation, relation_es in relation_types.items():
                doc_query = DocumentsSearch() \
                    .filter({'term': {relation_es: self.pid}})
                if pids := sorted_pids(doc_query):
                    documents[relation] = pids
        else:
            holdings = hold_query.count()
            items = item_query.count()
            loans = loan_query.count()
            acq_order_lines = acq_order_lines_query.count()
            documents = 0
            for relation_es in relation_types.values():
                doc_query = DocumentsSearch() \
                    .filter({'term': {relation_es: self.pid}})
                documents += doc_query.count()
        if holdings:
            links['holdings'] = holdings
        if items:
            links['items'] = items
        if loans:
            links['loans'] = loans
        if acq_order_lines:
            links['acq_order_lines'] = acq_order_lines
        if documents:
            links['documents'] = documents
        return links

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        if links := self.get_links_to_me():
            cannot_delete['links'] = links
        if self.harvested:
            cannot_delete['others'] = dict(harvested=True)
        return cannot_delete

    @classmethod
    def post_process(cls, dump):
        """Post process data after a dump.

        :param dump: a dictionary of a resulting Record dumps
        :return: a modified dictionary
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
        return Document.post_process(super().dumps(**kwargs))

    def index_contributions(self, bulk=False):
        """Index all attached contributions."""
        from ..contributions.api import Contribution, ContributionsIndexer
        from ..tasks import process_bulk_queue
        contributions_ids = []
        for contribution in self.get('contribution', []):
            ref = contribution['agent'].get('$ref')
            if not ref and (cont_pid := contribution['agent'].get('pid')):
                if bulk:
                    uid = Contribution.get_id_by_pid(cont_pid)
                    contributions_ids.append(uid)
                else:
                    contrib = Contribution.get_record_by_pid(cont_pid)
                    contrib.reindex()
        if contributions_ids:
            ContributionsIndexer().bulk_index(contributions_ids)
            process_bulk_queue.apply_async()

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
    def get_document_pids_by_issn(cls, issn_number: str):
        """Get pids of documents having the given ISSN.

        :param issn_number: the ISSN to search
        :return: the pids of the record having the given ISSN
        :rtype: generator
        """
        criteria = Q('term', nested_identifiers__type=IdentifierType.ISSN)
        criteria &= Q('term', nested_identifiers__value__raw=issn_number)
        es_documents = DocumentsSearch()\
            .filter('nested', path='nested_identifiers', query=criteria)\
            .source('pid').scan()
        for es_document in es_documents:
            yield es_document.pid

    def _expand_contributions(self, data):
        """Replace the $ref for contributions.

        :params data - dict: the contributions document data.
        :returns: the modified contributions document data.
        :rtype: dict
        """
        from ..contributions.api import Contribution
        new_contributions = []
        for contribution in data.get('contribution', []):
            if not contribution['agent'].get('$ref'):
                new_contributions.append(contribution)
            if mef_pid := contribution['agent'].get('pid'):
                if agent := Contribution.get_record_by_pid(mef_pid):
                    _type, _ = Contribution.get_type_and_pid_from_ref(
                        contribution['agent']['$ref'])
                    contribution['agent'] = agent.dumps_for_document()
                    contribution['agent']['primary_source'] = _type
                    new_contributions.append(contribution)
            elif contribution['agent'].get('$ref'):
                current_app.logger.error(
                    f'Unable to resolve contribution $ref '
                    f'{contribution["agent"].get("$ref")}'
                    f' for document {data.get("pid")}')
        if new_contributions:
            data['contribution'] = new_contributions
        return data

    def _expand_subjects(self, data):
        """Replace the $ref for subjects.

        :params data - dict: the subjects document data.
        :returns: the modified subject document data.
        :rtype: dict
        """
        from ..contributions.api import Contribution
        for subjects in ['subjects', 'subjects_imported']:
            for subject in data.get(subjects, []):
                subject_ref = subject.get('$ref')
                subject_type = subject.get('type')
                mef_pid = subject.get('pid')
                if subject_ref and subject_type in [
                    DocumentSubjectType.PERSON,
                    DocumentSubjectType.ORGANISATION
                ]:
                    contrib_data = Contribution.get_record_by_pid(mef_pid)
                    del subject['$ref']
                    subject.update(contrib_data)
        return data

    def replace_refs(self):
        """Replace $ref with real data."""
        data = deepcopy(self)
        data = self._expand_contributions(data)
        data = self._expand_subjects(data)

        if self.enable_jsonref:
            return _records_state.replace_refs(data)
        else:
            self

    def get_identifiers(self, filters=None, with_alternatives=False):
        """Get the document identifier object filtered by identifier types.

        :param filters: an array of identifiers types. If None or empty,
                        return all identifiers.
        :param with_alternatives: is the returned list should also contains
               the alternative identifiers of filtered original identifiers.
               If true, the returned list will contain only unique values.
        :return an array of `Identifiers` object corresponding to filters.
        """
        filters = [] or filters
        identifiers = {
            IdentifierFactory.create_identifier(data)
            for data in self.get('identifiedBy', [])
            if not filters or data.get('type') in filters
        }
        if with_alternatives:
            for identifier in list(identifiers):
                identifiers.update(identifier.get_alternatives())
        return identifiers

    @property
    def document_type(self):
        """Get first document type of document."""
        document_type = 'docmaintype_other'
        if document_types := self.get('type', []):
            document_type = document_types[0]['main_type']
            if document_subtype := document_types[0].get('subtype'):
                document_type = document_subtype
        return document_type

    @property
    def document_types(self):
        """All types of document."""
        document_types = []
        for document_type in self.get('type', []):
            main_type = document_type.get('main_type')
            if sub_type := document_type.get('subtype'):
                main_type = sub_type
            document_types.append(main_type)
        return document_types or ['docmaintype_other']

    def add_cover_url(self, url, dbcommit=False, reindex=False):
        """Adds electronicLocator with coverImage to document."""
        electronic_locators = self.get('electronicLocator', [])
        for electronic_locator in electronic_locators:
            e_content = electronic_locator.get('content')
            e_type = electronic_locator.get('type')
            if e_content == 'coverImage' and e_type == 'relatedResource':
                # don't add the same url
                if electronic_locator.get('url') == url:
                    return self, False
        electronic_locators.append({
            'content': 'coverImage',
            'type': 'relatedResource',
            'url': url
        })
        self['electronicLocator'] = electronic_locators
        self = self.update(
            data=self, commit=True, dbcommit=dbcommit, reindex=reindex)
        return self, True


class DocumentsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = Document

    @classmethod
    def _es_document(cls, record):
        """Get the document from the corresponding index.

        :param record: an item object
        :returns: the elasticsearch document or {}
        """
        try:
            es_item = current_search_client.get(
                DocumentsSearch.Meta.index, record.id)
            return es_item['_source']
        except NotFoundError:
            return {}

    def index(self, record):
        """Index an document."""
        # get previous indexed version
        es_document = self._es_document(record)

        # call the parent index method
        return_value = super().index(record)

        # index contributions
        # TODO: reindex contributions only if it has been touched
        record.index_contributions(bulk=True)

        # index document of the host document only if the title
        # has been changed
        # the comparison should be done on the dumps as _text is
        # added for indexing
        if not es_document \
           or (record.dumps().get('title') != es_document.get('title')):
            search = DocumentsSearch().filter(
                'term', partOf__document__pid=record.pid)
            if ids := [doc.meta.id for doc in search.source().scan()]:
                # reindex in background as the list can be huge
                self.bulk_index(ids)
        return return_value

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super().bulk_index(record_id_iterator, doc_type='doc')
