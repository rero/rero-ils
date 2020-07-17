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

import requests
from elasticsearch_dsl import A
from flask import current_app
from invenio_db import db
from requests import codes as requests_codes

from .models import PersonIdentifier, PersonMetadata
from ..api import IlsRecord, IlsRecordsIndexer, IlsRecordsSearch
from ..documents.api import DocumentsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ...utils import get_i18n_supported_languages, unique_list

# provider
PersonProvider = type(
    'PersonProvider',
    (Provider,),
    dict(identifier=PersonIdentifier, pid_type='pers')
)
# minter
person_id_minter = partial(id_minter, provider=PersonProvider)
# fetcher
person_id_fetcher = partial(id_fetcher, provider=PersonProvider)


class PersonsSearch(IlsRecordsSearch):
    """Mef person search."""

    class Meta():
        """Meta class."""

        index = 'persons'
        doc_types = None


class Person(IlsRecord):
    """Mef person class."""

    minter = person_id_minter
    fetcher = person_id_fetcher
    provider = PersonProvider
    model_cls = PersonMetadata

    @classmethod
    def get_record_by_ref(cls, ref):
        """Get a record from DB.

        If the record dos not exist get it from MEF and creat it.
        """
        pers = None
        ref_split = ref.split('/')
        ref_type = ref_split[-2]
        ref_pid = ref_split[-1]
        db.session.begin_nested()
        if ref_type == 'mef':
            pers = cls.get_record_by_pid(ref_pid)
        else:
            if ref_type == 'viaf':
                result = PersonsSearch().filter(
                    'term', viaf_pid=ref_pid
                ).source('pid').scan()
            else:
                result = PersonsSearch().filter(
                    {'term': {'{type}.pid'.format(type=ref_type): ref_pid}}
                ).source('pid').scan()
            try:
                pid = next(result).pid
                pers = cls.get_record_by_pid(pid)
            except StopIteration:
                pass
        if not pers:
            # We dit not find the record in DB get it from MEF and create it.
            try:
                data = cls._get_mef_data_by_type(ref_pid, ref_type)
                metadata = data['metadata']
                # Register MEF person
                if '$schema' in metadata:
                    del metadata['$schema']
                # we have to commit because create
                # uses db.session.begin_nested
                pers = cls.create(metadata, dbcommit=True)
            except Exception as err:
                db.session.rollback()
                current_app.logger.error('Get MEF record: {type}:{pid}'.format(
                    type=ref_type,
                    pid=ref_pid
                ))
                current_app.logger.error(err)
                return None
        db.session.commit()
        if pers:
            pers.reindex()
        return pers

    def dumps_for_document(self):
        """Transform the record into document contribution format."""
        return self._get_contribution_for_document()

    @classmethod
    def _get_mef_data_by_type(cls, pid, pid_type):
        """Request MEF REST API in JSON format."""
        url = current_app.config.get('RERO_ILS_MEF_URL')
        if pid_type == 'mef':
            mef_url = "{url}?q=pid:{pid}".format(url=url, pid=pid)
        else:
            if pid_type == 'viaf':
                mef_url = "{url}?q=viaf_pid:{pid}".format(url=url, pid=pid)
            else:
                mef_url = "{url}?q={type}.pid:{pid}".format(
                    url=url,
                    type=pid_type,
                    pid=pid
                )
        request = requests.get(url=mef_url, params=dict(resolve=1, sources=1))
        if request.status_code == requests_codes.ok:
            data = request.json().get('hits', {}).get('hits', [None])
            return data[0]
        else:
            current_app.logger.error(
                'Mef resolver no metadata: {result} {url}'.format(
                    result=request.json(),
                    url=mef_url
                )
            )
            raise Exception('unable to resolve')

    # TODO: if I delete the id the mock is not working any more ????
    def _get_mef_value(self, key, default=None):
        """Get the first value for given key among MEF source list."""
        value = None
        sources = current_app.config.get('RERO_ILS_PERSONS_SOURCES', [])
        for source in sources:
            value = self.get(source, {}).get(key, default)
            if value:
                return value

    def _get_mef_localized_value(self, key, language):
        """Get the 1st localized value for given key among MEF source list."""
        order = current_app.config.get('RERO_ILS_PERSONS_LABEL_ORDER', [])
        source_order = order.get(language, order.get(order['fallback'], []))
        for source in source_order:
            value = self.get(source, {}).get(key, None)
            if value:
                return value
        return self.get(key, None)

    def _get_contribution_for_document(self):
        """Get contribution for document."""
        agent = {
            'type': 'bf:Person',
            'pid': self.pid
        }
        for language in get_i18n_supported_languages():
            agent[
                'authorized_access_point_{language}'.format(language=language)
            ] = self._get_mef_localized_value(
                'authorized_access_point_representing_a_person', language
            )
        # date
        date_of_birth = self._get_mef_value('date_of_birth', '')
        if date_of_birth:
            agent['date_of_birth'] = date_of_birth
        date_of_death = self._get_mef_value('date_of_death', '')
        if date_of_death:
            agent['date_of_death'] = date_of_death
        # TODO: variant_name
        variant_person = []
        for source in self['sources']:
            if 'variant_name_for_person' in self[source]:
                variant_person = variant_person +\
                    self[source]['variant_name_for_person']
        if variant_person:
            agent['variant_name'] = unique_list(variant_person)

        return agent

    @property
    def organisation_pids(self):
        """Get organisations pids."""
        organisations = set()
        search = DocumentsSearch().filter('term', contribution__pid=self.pid)
        size = current_app.config.get(
            'RERO_ILS_AGGREGATION_SIZE'
        ).get('organisations')
        agg = A('terms',
                field='holdings.organisation.organisation_pid', size=size)
        search.aggs.bucket('organisation', agg)
        results = search.execute()
        for result in results.aggregations.organisation.buckets:
            if result.doc_count:
                organisations.add(result.key)
        return list(organisations)

    def get_authorized_access_point(self, language):
        """Get localized authorized_access_point.

        :param language: language for authorized access point.
        :returns: authorized access point in given lamguage.
        """
        return self._get_mef_localized_value(
            key='authorized_access_point_representing_a_person',
            language=language
        )


class PersonsIndexer(IlsRecordsIndexer):
    """Person indexing class."""

    record_cls = Person

    def bulk_index(self, record_id_iterator):
        """Bulk index records.

        :param record_id_iterator: Iterator yielding record UUIDs.
        """
        super(PersonsIndexer, self).bulk_index(record_id_iterator,
                                               doc_type='pers')
