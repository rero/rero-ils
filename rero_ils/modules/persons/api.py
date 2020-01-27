# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

from elasticsearch_dsl import A
from flask import current_app
from invenio_db import db
from invenio_search.api import RecordsSearch
from requests import codes as requests_codes
from requests import get as requests_get

from .models import PersonIdentifier
from ..api import IlsRecord
from ..documents.api import DocumentsSearch
from ..fetchers import id_fetcher
from ..minters import id_minter
from ..providers import Provider
from ...utils import unique_list

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


class PersonsSearch(RecordsSearch):
    """Mef person search."""

    class Meta():
        """Meta class."""

        index = 'persons'


class Person(IlsRecord):
    """Mef person class."""

    minter = person_id_minter
    fetcher = person_id_fetcher
    provider = PersonProvider

    @classmethod
    def get_record_by_mef_pid(cls, pid):
        """Get record using MEF REST API."""
        try:
            db.session.begin_nested()
            rec = cls.get_record_by_pid(pid)
            if not rec:
                # No data found: request on MEF URL
                data = cls._get_mef_record(pid)
                # Register MEF person
                metadata = data.get('metadata')
                if '$schema' in metadata:
                    del metadata['$schema']
                rec = cls.create(metadata, dbcommit=True)
        except Exception as err:
            db.session.rollback()
            current_app.logger.error('ERROR get MEF record: {pid}'.format(
                pid=pid
            ))
            return None
        db.session.commit()
        rec.reindex()
        return rec

        rec = cls.get_record_by_pid(pid)
        if not rec:
            # No data found: request on MEF URL
            data = cls._get_mef_record(pid)
            # Register MEF person
            metadata = data.get('metadata')
            if '$schema' in metadata:
                del metadata['$schema']
            rec = cls.create(metadata, dbcommit=True)
        return rec

    def dumps_for_document(self):
        """Transform the record into document author format."""
        return self._get_author_for_document()

    @classmethod
    def _get_mef_record(cls, pid):
        """Request MEF REST API in JSON format."""
        url = "{url}{pid}".format(
            url=current_app.config.get('RERO_ILS_MEF_URL'),
            pid=pid)
        request = requests_get(
            url=url,
            params=dict(
                resolve=1,
                sources=1
            ))
        if request.status_code == requests_codes.ok:
            return request.json()
        else:
            current_app.logger.error(
                'Mef resolver no metadata: {result} {url}'.format(
                    result=request.json(),
                    url=url
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

    def _get_i18n_supported_languages(self):
        """Get defined languages from config."""
        languages = [current_app.config.get('BABEL_DEFAULT_LANGUAGE')]
        i18n_languages = current_app.config.get('I18N_LANGUAGES')
        return languages + [ln[0] for ln in i18n_languages]

    def _get_author_for_document(self):
        """."""
        author = {
            'type': 'person',
            'pid': self.pid
        }
        for language in self._get_i18n_supported_languages():
            author[
                'name_{language}'.format(language=language)
            ] = self._get_mef_localized_value(
                'preferred_name_for_person', language
            )
        # date
        date_of_birth = self._get_mef_value('date_of_birth', '')
        date_of_death = self._get_mef_value('date_of_death', '')
        if date_of_birth or date_of_death:
            date = '{date_of_birth}-{date_of_death}'.format(
                date_of_birth=date_of_birth,
                date_of_death=date_of_death
            )
            author['date'] = date
        # variant_name
        variant_person = []
        for source in self['sources']:
            if 'variant_name_for_person' in self[source]:
                variant_person = variant_person +\
                    self[source]['variant_name_for_person']
        if variant_person:
            author['variant_name'] = unique_list(variant_person)
        return author

    @property
    def organisation_pids(self):
        """Get organisations pids."""
        organisations = set()
        search = DocumentsSearch().filter('term', authors__pid=self.pid)
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
