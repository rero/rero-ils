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

"""Import from extern resources."""


from __future__ import absolute_import, print_function

import pickle
from datetime import timedelta
from operator import itemgetter

import requests
from dojson.contrib.marc21.utils import create_record
from flask import abort, current_app, jsonify, url_for
from lxml import etree
from redis import Redis
from six import BytesIO

from ..documents.dojson.contrib.marc21tojson import marc21_dnb, marc21_kul, \
    marc21_loc, marc21_slsp, marc21_ugent
from ..documents.dojson.contrib.unimarctojson import unimarc


class Import(object):
    """Import class."""

    name = ''
    url = ''
    url_api = ''
    search = {}
    to_json_processor = None
    status_code = 444
    max = 50

    def __init__(self):
        """Init Import class."""
        assert self.name
        assert self.url
        assert self.url_api
        assert self.search
        assert self.search.get('anywhere')
        assert self.to_json_processor
        self.init_results()
        self.cache = Redis.from_url(current_app.config.get(
            'RERO_IMPORT_CACHE'
        ))
        self.cache_expire = current_app.config.get('RERO_IMPORT_CACHE_EXPIRE')

    def init_results(self):
        """Init results."""
        self.results = {
            'aggregations': {},
            'hits': {
                'hits': [],
                'total': {
                    'value': 0,
                    'relation': 'eq'
                },
                'remote_total': 0
            },
            'links': {},
            'permissions': {}

        }
        self.data = []

    @property
    def response(self):
        """Jsonify results."""
        return jsonify(self.results), self.status_code

    def get_id(self, json_data):
        """Get id.

        :param id: json document
        :return: id of the record
        """
        return json_data.get('001')

    def get_link(self, id):
        """Get direct link to record.

        :param id: id to use for the link
        :return: url for id
        """
        url_api = self.url_api.format(
            url=self.url,
            max=1,
            what=id,
            relation='all',
            where=self.search.get('recordid')
        )
        return url_api

    def get_marc21_link(self, id):
        """Get direct link to marc21 record.

        Has to be addaped in each sub class!
        :param id: id to use for the link
        :return: url for id
        """
        return None

    def calculate_aggregations_add(self, type, data, id):
        """Add data to aggregations_creation.

        :param type: type of the aggregation
        :param data: data for the aggregation
        :param id: id for the type
        """
        if data:
            ids_indexes = self.aggregations_creation[type].get(
                data,
                {'ids': set()}
            )
            ids_indexes['ids'].add(id)
            self.aggregations_creation[type][data] = ids_indexes

    def calculate_aggregations_add_sub(self, type, data, sub_type, sub_data,
                                       id):
        """Add data to aggregations_creation.

        :param type: type of the aggregation
        :param data: data for the aggregation
        :param sub_type: type of the aggregation
        :param sub_data: data for the aggregation
        :param id: id for the type
        """
        if data:
            ids_indexes = self.aggregations_creation[type].get(
                data,
                {'ids': set(), 'sub_type': sub_type, 'sub': {}}
            )
            ids_indexes['ids'].add(id)
            # check if we have data for subtype
            if sub_data:
                ids_indexes['sub'].setdefault(sub_data, set()).add(id)
            self.aggregations_creation[type][data] = ids_indexes

    def calculate_aggregations(self, record, id):
        """Calculate aggregations.

        :param record: record to create aggregation from
        :param id: id for the record
        :param indexd: index of the record
        """
        for document_type in record['type']:
            self.calculate_aggregations_add_sub(
                type='document_type',
                data=document_type['main_type'],
                sub_type='document_subtype',
                sub_data=document_type.get('subtype'),
                id=id
            )

        provision_activitys = record.get('provisionActivity', [])
        for provision_activity in provision_activitys:
            date = provision_activity.get('startDate')
            self.calculate_aggregations_add('year', date, id)

        contribution = record.get('contribution', [])
        for agent in contribution:
            name = agent.get('agent', {}).get('preferred_name')
            self.calculate_aggregations_add('author', name, id)

        languages = record.get('language', [])
        for language in languages:
            lang = language.get('value')
            self.calculate_aggregations_add('language', lang, id)

    def create_aggregations(self, results):
        """Create aggregations.

        :param results: dictionary with the results in hits hits
        :return: dictionary with results and added aggregations
        """
        self.aggregations_creation = {
            'document_type': {},
            'author': {},
            'year': {},
            'language': {}
        }
        results['aggregations'] = {}
        for data in results['hits']['hits']:
            self.calculate_aggregations(
                data['metadata'],
                data['id']
            )
        for agg, values in self.aggregations_creation.items():
            buckets = []
            for key, value in values.items():
                ids = value['ids']
                bucket_data = {
                    'ids': list(ids),
                    'doc_count': len(ids),
                    'key': str(key),
                    'doc_count_error_upper_bound': 0,
                    'sum_other_doc_count': 0
                }
                subs = value.get('sub')
                if subs:
                    sub_buckets = []
                    for sub_key, sub_value in subs.items():
                        sub_buckets.append({
                            'ids': list(sub_value),
                            'doc_count': len(sub_value),
                            'key': sub_key
                        })
                        sub_buckets.sort(
                            key=lambda e: (-e['doc_count'], e['key']))
                        bucket_data[value.get('sub_type')] = {
                            'buckets': sub_buckets
                        }
                buckets.append(bucket_data)
            if agg == 'year':
                buckets.sort(key=itemgetter('key'), reverse=True)
            else:
                buckets.sort(key=lambda e: (-e['doc_count'], e['key']))
            if buckets:
                results['aggregations'][agg] = {'buckets': buckets}
        results['hits']['total']['value'] = len(results['hits']['hits'])
        return results

    def filter_records(self, results, ids):
        """Filter records by ids.

        :param results: dictionary with the results in hits hits
        :param ids: list with ids to filter
        :return: dictionary with results filtered by ids and
                  adapted aggregations
        """
        hits = results['hits']['hits']
        hits = list(filter(lambda hit: hit['id'] in ids, hits))
        results['hits']['hits'] = hits
        self.create_aggregations(results)
        return results

    def get_ids_for_aggregation(self, results, aggregation, key):
        """Get ids for aggregation.

        :param results: dictionary with the results in hits hits
        :param aggregation: whitch aggregation ro use to use to get the ids
        :param key: whitch key in aggregation to use to get the ids
        :return: list of ids
        """
        ids = []
        buckets = results.get('aggregations').get(
            aggregation, {}
        ).get('buckets', [])
        bucket = list(
            filter(lambda bucket: bucket['key'] == str(key), buckets))
        if bucket:
            ids = bucket[0]['ids']
        return ids

    def get_ids_for_aggregation_sub(self, results, agg, key, sub_agg, sub_key):
        """Get ids for aggregation.

        :param results: dictionary with the results in hits hits
        :param agg: which aggregation to use to use to get the ids
        :param key: which key in aggregation to use to get the ids
        :param sub_agg: which aggregation to use to use to get the ids
        :param sub_key: which sub_key from key in aggregation to use
                        to get the ids
        :return: list of ids
        """
        ids = []
        buckets = results.get('aggregations').get(agg, {}).get('buckets', [])
        bucket = list(
            filter(lambda bucket: bucket['key'] == str(key), buckets))
        if bucket:
            sub_buckets = bucket[0].get(sub_agg, {}).get('buckets', [])
            sub_bucket = list(
                filter(
                    lambda sub_bucket: sub_bucket['key'] == str(sub_key),
                    sub_buckets
                )
            )
            ids = sub_bucket[0]['ids']
        return ids

    def search_records(self, what, relation, where='anywhere', max=0,
                       no_cache=False):
        """Get the records.

        :param what: what term to search
        :param relation: relation for what and where
        :param where: in witch index to search
        :param max: maximum records to search
        :param no_cache: do not use cache if true
        """
        if max == 0:
            max = self.max
        if self.name == 'LOC' and relation == "all":
            relation = "="
        self.init_results()
        if not what:
            return self.results, 200
        try:
            cache_key = f'{self.name}_{what}_{relation}_{where}_{max}'
            cache = self.cache.get(cache_key)
            if cache and not no_cache:
                cache_data = pickle.loads(cache)
                self.results['hits'] = cache_data['hits']
                self.data = cache_data['data']
            else:
                url_api = self.url_api.format(
                    url=self.url,
                    max=max,
                    what=what,
                    relation=relation,
                    where=self.search.get(where)
                )
                response = requests.get(url_api)
                if not response.ok:
                    self.status_code = 502
                    response = {
                        'metadata': {},
                        'errors': {
                            'code': self.status_code,
                            'title': f'{self.name}: Bad status code!',
                            'detail': f'Status code: {response.status_code}'
                        }
                    }
                    current_app.logger.error(
                        '{title}: {detail}'.format(
                            title=response.get('title'),
                            detail=response.get('detail')))

                else:
                    def _split_stream(stream):
                        """Yield record elements from given stream."""
                        for _, element in etree.iterparse(
                                stream,
                                tag='{http://www.loc.gov/zing/srw/}'
                                    'record'):
                            yield element

                    xml_records = _split_stream(BytesIO(response.content))

                    for xml_record in xml_records:
                        # convert xml in marc json
                        json_data = create_record(xml_record)
                        # Some BNF records are empty hmm...
                        if not json_data.values():
                            continue

                        # convert marc json to local json format
                        record = self.to_json_processor(json_data)

                        id = self.get_id(json_data)
                        if record and id:
                            data = {
                                'id': id,
                                'links': {
                                    'self': self.get_link(id),
                                    'marc21': self.get_marc21_link(id)
                                },
                                'metadata': record,
                                'source': self.name
                            }
                            self.data.append(json_data)
                            self.results['hits']['hits'].append(data)
                            self.results['hits']['remote_total'] = int(
                                etree.parse(BytesIO(response.content))
                                .find('{*}numberOfRecords').text
                            )

            self.results['hits']['total']['value'] = len(
                self.results['hits']['hits'])
            if self.results['hits']['total']['value'] == 0:
                self.status_code = 404
                self.results['errors'] = {
                    'code': self.status_code,
                    'title': f'{self.name}: Not found: '
                             f'{where} {relation} {what}'
                    }
            else:
                cache_data = {
                    'hits': self.results['hits'],
                    'data': self.data
                }
                self.cache.setex(
                    cache_key,
                    timedelta(minutes=self.cache_expire),
                    value=pickle.dumps(cache_data)
                )
                self.create_aggregations(self.results)
                self.status_code = 200

        except Exception as error:
            current_app.logger.error(
                '{title}: {detail}'.format(
                    title=f'{self.name} Error!',
                    detail=f'Error: {error}'
                )
            )
            abort(500, description=f'Error: {error}')
        return self.results, self.status_code


class BnfImport(Import):
    """Import class for BNF."""

    name = 'BNF'
    url = 'http://catalogue.bnf.fr'
    url_api = '{url}/api/SRU?'\
              'version=1.2&operation=searchRetrieve'\
              '&recordSchema=unimarcxchange-anl&maximumRecords={max}'\
              '&startRecord=1&query={where} {relation} "{what}"'

    # https://www.bnf.fr/sites/default/files/2019-04/tableau_criteres_sru.pdf
    search = {
        'ean': 'bib.ean',
        'anywhere': 'bib.anywhere',
        'author': 'bib.author',
        'title': 'bib.title',
        'doctype': 'bib.doctype',
        'recordid': 'bib.recordid',
        'isbn': 'bib.isbn',
        'issn': 'bib.issn',
        'date': 'bib.date'
    }

    to_json_processor = unimarc.do

    def get_marc21_link(self, id):
        """Get direct link to marc21 record.

        :param id: id to use for the link
        :return: url for id
        """
        args = {
            'id': id,
            '_external': True,
            current_app.config.get(
                'REST_MIMETYPE_QUERY_ARG_NAME', 'format'): 'marc'
        }
        return url_for('api_imports.import_bnf_record', **args)


class LoCImport(Import):
    """Import class for Library of Congress."""

    name = 'LOC'
    url = 'http://lx2.loc.gov:210'
    url_api = '{url}/lcdb?'\
              'version=1.2&operation=searchRetrieve'\
              '&recordSchema=marcxml&maximumRecords={max}'\
              '&startRecord=1&query={where} {relation} "{what}"'

    # http://www.loc.gov/standards/sru/resources/lcServers.html
    search = {
        'ean': 'dc.identifier',
        'anywhere': 'anywhere',
        'author': 'dc.creator',
        'title': 'dc.title',
        'doctype': 'dc.type',
        'recordid': 'dc.identifier',
        'isbn': 'dc.identifier',
        'issn': 'dc.identifier',
        'date': 'dc.date'
    }

    to_json_processor = marc21_loc.do

    # For LoC record, let's take the recordID in Tag 010 $a
    def get_id(self, json_data):
        """Get id.

        :param id: json document
        :return: id of the record
        """
        if json_data.get('010__'):
            return json_data.get('010__').get('a').strip()

    def get_marc21_link(self, id):
        """Get direct link to marc21 record.

        :param id: id to use for the link
        :return: url for id
        """
        args = {
            'id': id,
            '_external': True,
            current_app.config.get(
                'REST_MIMETYPE_QUERY_ARG_NAME', 'format'): 'marc'
        }
        return url_for('api_imports.import_loc_record', **args)


class DNBImport(Import):
    """Import class for DNB."""

    name = 'DNB'
    url = 'https://services.dnb.de'
    url_api = '{url}/sru/dnb?'\
              'version=1.1&operation=searchRetrieve'\
              '&recordSchema=MARC21-xml&maximumRecords={max}'\
              '&startRecord=1&query={where} {relation} "{what}"'

    # https://www.dnb.de/EN/Professionell/Metadatendienste/Datenbezug/SRU/sru_node.html
    search = {
        'ean': 'dnb.num',
        'anywhere': 'dnb.woe',
        'author': 'dnb.atr',
        'title': 'dnb.tit',
        'doctype': 'dnb.mat',
        'recordid': 'dnb.num',
        'isbn': 'dnb.num',
        'issn': 'dnb.num',
        'date': 'dnb.jhr'
    }

    to_json_processor = marc21_dnb.do

    def get_marc21_link(self, id):
        """Get direct link to marc21 record.

        :param id: id to use for the link
        :return: url for id
        """
        args = {
            'id': id,
            '_external': True,
            current_app.config.get(
                'REST_MIMETYPE_QUERY_ARG_NAME', 'format'): 'marc'
        }
        return url_for('api_imports.import_dnb_record', **args)


class SLSPImport(Import):
    """Import class for SLSP."""

    name = 'SLSP'
    url = 'https://swisscovery.slsp.ch'
    url_api = '{url}/view/sru/41SLSP_NETWORK?'\
              'version=1.2&operation=searchRetrieve'\
              '&recordSchema=marcxml&maximumRecords={max}'\
              '&startRecord=1&query={where} {relation} "{what}"'

    # https://slsp.ch/fr/metadata
    # https://developers.exlibrisgroup.com/alma/integrations/sru/
    search = {
        'anywhere': 'alma.all_for_ui',
        'author': 'alma.author',
        'title': 'alma.title',
        'recordid': 'alma.all_for_ui',
        'isbn': 'alma.isbn',
        'issn': 'alma.issn',
        'date': 'alma.date'
    }

    to_json_processor = marc21_slsp.do

    def get_marc21_link(self, id):
        """Get direct link to marc21 record.

        :param id: id to use for the link
        :return: url for id
        """
        args = {
            'id': id,
            '_external': True,
            current_app.config.get(
                'REST_MIMETYPE_QUERY_ARG_NAME', 'format'): 'marc'
        }
        return url_for('api_imports.import_slsp_record', **args)


class UGentImport(Import):
    """Import class for Univ. of Gent (Belgium)."""

    name = 'UGent'
    url = 'https://lib.ugent.be/sru'
    url_api = '{url}?'\
              'version=1.1&operation=searchRetrieve'\
              '&recordSchema=marcxml&maximumRecords={max}'\
              '&startRecord=1&query={where} {relation} "{what}"'

    # https://lib.ugent.be/sru
    search = {
        'ean': 'isbn',
        'anywhere': 'all',
        'author': 'author',
        'title': 'title',
        'doctype': 'dc.type',
        'recordid': 'all',
        'isbn': 'isbn',
        'issn': 'issn',
        'date': 'year'
    }

    to_json_processor = marc21_ugent.do

    def get_id(self, json_data):
        """Get id.

        :param id: json document
        :return: id of the record
        """
        id = None
        if json_data.get('001'):
            id = json_data.get('001')
        elif json_data.get('090__'):
            id = json_data.get('090__').get('a').strip()
        return id

    def get_marc21_link(self, id):
        """Get direct link to marc21 record.

        :param id: id to use for the link
        :return: url for id
        """
        args = {
            'id': id,
            '_external': True,
            current_app.config.get(
                'REST_MIMETYPE_QUERY_ARG_NAME', 'format'): 'marc'
        }
        return url_for('api_imports.import_ugent_record', **args)


class KULImport(Import):
    """Import class for KULeuven."""

    name = 'KUL'
    url = 'https://eu.alma.exlibrisgroup.com'
    url_api = '{url}/view/sru/32KUL_LIBIS_NETWORK?'\
              'version=1.2&operation=searchRetrieve'\
              '&recordSchema=marcxml&maximumRecords={max}'\
              '&startRecord=1&query={where} {relation} "{what}"'

    # https://developers.exlibrisgroup.com/alma/integrations/sru/
    search = {
        'anywhere': 'alma.all_for_ui',
        'author': 'alma.creator',
        'title': 'alma.title',
        'recordid': 'alma.all_for_ui',
        'isbn': 'alma.isbn',
        'issn': 'alma.issn',
        'date': 'alma.date'
    }

    to_json_processor = marc21_kul.do

    def get_marc21_link(self, id):
        """Get direct link to marc21 record.

        :param id: id to use for the link
        :return: url for id
        """
        args = {
            'id': id,
            '_external': True,
            current_app.config.get(
                'REST_MIMETYPE_QUERY_ARG_NAME', 'format'): 'marc'
        }
        return url_for('api_imports.import_kul_record', **args)
