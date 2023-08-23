# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2023 RERO
# Copyright (C) 2019-2023 UCLouvain
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

from elasticsearch.exceptions import NotFoundError
from elasticsearch_dsl import Q
from flask import current_app
from invenio_circulation.search.api import search_by_pid
from invenio_search import current_search_client
from jsonschema.exceptions import ValidationError

from rero_ils.modules.acquisition.acq_order_lines.api import \
    AcqOrderLinesSearch
from rero_ils.modules.api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from rero_ils.modules.commons.identifiers import IdentifierFactory, \
    IdentifierType
from rero_ils.modules.fetchers import id_fetcher
from rero_ils.modules.local_fields.extensions import \
    DeleteRelatedLocalFieldExtension
from rero_ils.modules.minters import id_minter
from rero_ils.modules.operation_logs.extensions import \
    OperationLogObserverExtension
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.providers import Provider
from rero_ils.modules.utils import sorted_pids

from .dumpers import document_indexer_dumper, document_replace_refs_dumper
from .extensions import AddMEFPidExtension, EditionStatementExtension, \
    ProvisionActivitiesExtension, SeriesStatementExtension, TitleExtension
from .models import DocumentIdentifier, DocumentMetadata

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

    def by_entity(self, entity, subjects=True, imported_subjects=True,
                  genre_forms=True):
        """Build a search to get hits related to an entity.

        :param entity: the entity record to search.
        :param subjects: search on `subject` field.
        :param imported_subjects: search on `imported_subject` field.
        :param genre_forms: search on `genre_forms` field.
        :returns: An ElasticSearch query to get hits related the entity.
        :rtype: `elasticsearch_dsl.Search`
        """
        field = f'contribution.entity.pids.{entity.resource_type}'
        filters = Q('term', **{field: entity.pid})
        if subjects:
            field = f'subjects.entity.pids.{entity.resource_type}'
            filters |= Q('term', **{field: entity.pid})
        if imported_subjects:
            field = f'subjects_imported.pids.{entity.resource_type}'
            filters |= Q('term', **{field: entity.pid})
        if genre_forms:
            field = f'genreForm.entity.pids.{entity.resource_type}'
            filters |= Q('term', **{field: entity.pid})
        return self.filter(filters)

    def by_library_pid(self, library_pid):
        """Build a search to get hits related to a library pid.

        :param library_pid: string - the library pid to filter with
        :returns: An ElasticSearch query to get hits related the entity.
        :rtype: `elasticsearch_dsl.Search`
        """
        return self.filter(
            'term', holdings__organisation__library_pid=library_pid)


class Document(IlsRecord):
    """Document class."""

    minter = document_id_minter
    fetcher = document_id_fetcher
    provider = DocumentProvider
    model_cls = DocumentMetadata
    # disable legacy replace refs
    enable_jsonref = False

    _extensions = [
        OperationLogObserverExtension(),
        AddMEFPidExtension('subjects', 'contribution', 'genreForm'),
        ProvisionActivitiesExtension(),
        SeriesStatementExtension(),
        EditionStatementExtension(),
        TitleExtension(),
        DeleteRelatedLocalFieldExtension()
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
                if part_of := self.get('partOf', []):
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
    def get_n_available_holdings(cls, pid, org_pid=None):
        """Get the number of available and electronic holdings.

        :param pid: str - the document pid.
        :param org_pid: str - the organisation pid.
        :returns: int, int - the number of available and electronic holdings.
        """
        from rero_ils.modules.holdings.api import HoldingsSearch

        # create the holding search query
        holding_query = HoldingsSearch().available_query()

        # filter by the current document
        filters = Q('term', document__pid=pid)

        # filter by organisation
        if org_pid:
            filters &= Q('term', organisation__pid=org_pid)
        holding_query = holding_query.filter(filters)

        # get the number of electronic holdings
        n_electronic_holdings = holding_query\
            .filter('term', holdings_type='electronic')

        return holding_query.count(), n_electronic_holdings.count()

    @classmethod
    def get_available_item_pids(cls, pid, org_pid=None):
        """Get the list of the available item pids.

        :param pid: str - the document pid.
        :param org_pid: str - the organisation pid.
        :returns: [str] - the list of the available item pids.
        """
        from rero_ils.modules.items.api import ItemsSearch

        # create the item query
        items_query = ItemsSearch().available_query()

        # filter by the current document
        filters = Q('term', document__pid=pid)

        # filter by organisation
        if org_pid:
            filters &= Q('term', organisation__pid=org_pid)

        return [
            hit.pid for hit in items_query.filter(filters).source('pid').scan()
        ]

    @classmethod
    def get_item_pids_with_active_loan(cls, pid, org_pid=None):
        """Get the list of items pids that have active loans.

        :param pid: str - the document pid.
        :param org_pid: str - the organisation pid.
        :returns: [str] - the list of the item pids having active loans.
        """
        from rero_ils.modules.loans.api import LoansSearch

        loan_query = LoansSearch().unavailable_query()

        # filter by the current document
        filters = Q('term', document_pid=pid)

        # filter by organisation
        if org_pid:
            filters &= Q('term', organisation__pid=org_pid)

        loan_query = loan_query.filter(filters)

        return [
            hit.item_pid.value for hit in loan_query.source('item_pid').scan()
        ]

    @classmethod
    def is_available(cls, pid, view_code=None):
        """Get availability for document.

        Note: if the logic has to be changed here please check also for items
        and holdings availability.

        :param pid: str - document pid value.
        :param view_code: str - the view code.
        """
        # get the organisation pid corresponding to the view code
        org_pid = None
        if view_code != current_app.config.get(
                'RERO_ILS_SEARCH_GLOBAL_VIEW_CODE'):
            org_pid = Organisation.get_record_by_viewcode(view_code)['pid']

        # -------------- Holdings --------------------
        # get the number of available and electronic holdings
        n_available_holdings, n_electronic_holdings = \
            cls.get_n_available_holdings(pid, org_pid)

        # available if an electronic holding exists
        if n_electronic_holdings:
            return True

        # unavailable if no holdings exists
        if not n_available_holdings:
            return False

        # -------------- Items --------------------
        # get the available item pids
        available_item_pids = cls.get_available_item_pids(pid, org_pid)

        # unavailable if no items exists
        if not available_item_pids:
            return False

        # --------------- Loans -------------------
        # get item pids that have active loans
        unavailable_item_pids = \
            cls.get_item_pids_with_active_loan(pid, org_pid)

        # available if at least one item don't have active loan
        return bool(set(available_item_pids) - set(unavailable_item_pids))

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
        from ..holdings.api import HoldingsSearch
        from ..items.api import ItemsSearch
        from ..loans.models import LoanState
        from ..local_fields.api import LocalFieldsSearch
        hold_query = HoldingsSearch().filter('term', document__pid=self.pid)
        item_query = ItemsSearch().filter('term', document__pid=self.pid)
        loan_query = search_by_pid(
            document_pid=self.pid,
            exclude_states=[LoanState.CANCELLED, LoanState.ITEM_RETURNED]
        )
        acq_order_lines_query = AcqOrderLinesSearch() \
            .filter('term', document__pid=self.pid)
        local_fields_query = LocalFieldsSearch()\
            .get_local_fields(self.provider.pid_type, self.pid)
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
            local_fields = sorted_pids(local_fields_query)
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
            local_fields = local_fields_query.count()
            documents = 0
            for relation_es in relation_types.values():
                doc_query = DocumentsSearch() \
                    .filter({'term': {relation_es: self.pid}})
                documents += doc_query.count()

        links = {
            'holdings': holdings,
            'items': items,
            'loans': loans,
            'acq_order_lines': acq_order_lines,
            'documents': documents,
            'local_fields': local_fields
        }
        return {k: v for k, v in links.items() if v}

    def reasons_not_to_delete(self):
        """Get reasons not to delete record."""
        cannot_delete = {}
        links = self.get_links_to_me()
        # related LocalFields isn't a reason to block suppression
        links.pop('local_fields', None)
        if links:
            cannot_delete['links'] = links
        if self.harvested:
            cannot_delete['others'] = dict(harvested=True)
        return cannot_delete

    def index_contributions(self, bulk=False):
        """Index all attached contributions."""
        from rero_ils.modules.entities.remote_entities.api import \
            RemoteEntitiesIndexer, RemoteEntity

        from ..tasks import process_bulk_queue
        contributions_ids = []
        for contribution in self.get('contribution', []):
            ref = contribution['entity'].get('$ref')
            if not ref and (cont_pid := contribution['entity'].get('pid')):
                if bulk:
                    uid = RemoteEntity.get_id_by_pid(cont_pid)
                    contributions_ids.append(uid)
                else:
                    contrib = RemoteEntity.get_record_by_pid(cont_pid)
                    contrib.reindex()
        if contributions_ids:
            RemoteEntitiesIndexer().bulk_index(contributions_ids)
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
            if (
                e_content == 'coverImage'
                and e_type == 'relatedResource'
                and electronic_locator.get('url') == url
            ):
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

    def resolve(self):
        """Resolve references data.

        Uses the dumper to do the job.
        Mainly used by the `resolve=1` URL parameter.

        :returns: a fresh copy of the resolved data.
        """
        return self.dumps(document_replace_refs_dumper)


class DocumentsIndexer(IlsRecordsIndexer):
    """Indexing documents in Elasticsearch."""

    record_cls = Document
    # data dumper for indexing
    record_dumper = document_indexer_dumper

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
