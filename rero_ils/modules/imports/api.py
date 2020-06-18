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

from ..documents.dojson.contrib.unimarctojson import unimarc


class Import(object):
    """Import class."""

    name = ''
    url = None
    url_api = None
    search = {}
    marc_to_json = None
    status_code = 444
    max = 50

    def __init__(self):
        """Init Import class."""
        assert self.name
        assert self.url
        assert self.url_api
        assert self.search
        assert self.search.get('anywhere')
        assert self.marc_to_json
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
                'total': 0,
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
        """Get id."""
        return json_data.get('001')

    def get_link(self, id):
        """Get direct link to record.

        :param id: id to use for the link
        :returns: url for id
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
        :returns: url for id
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
                {'ids': [], 'indexes': []}
            )
            ids_indexes['ids'].append(id)
            self.aggregations_creation[type][data] = ids_indexes

    def calculate_aggregations(self, record, id):
        """Calculate aggregations.

        :param record: record to create aggregation from
        :param id: id for the record
        :param indexd: index of the record
        """
        type = record.get('type')
        self.calculate_aggregations_add('type', type, id)

        provision_activitys = record.get('provisionActivity', [])
        for provision_activity in provision_activitys:
            date = provision_activity.get('startDate')
            self.calculate_aggregations_add('year', date, id)

        authors = record.get('authors', [])
        for author in authors:
            name = author.get('name')
            self.calculate_aggregations_add('author', name, id)

    def create_aggregations(self, results):
        """Create aggregations.

        :param results: dictionary with the results in hits hits
        :returns: dictionary with results and added aggregations
        """
        self.aggregations_creation = {
            'type': {},
            'author': {},
            'year': {}
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
                ids = list(set(value['ids']))
                buckets.append({
                    'doc_count': len(ids),
                    'ids': ids,
                    'key': str(key)
                })
            if agg == 'year':
                buckets.sort(key=itemgetter('key'), reverse=True)
            else:
                buckets.sort(key=lambda e: (-e['doc_count'], e['key']))

            if buckets:
                results['aggregations'][agg] = {'buckets': buckets}
        results['hits']['total'] = len(results['hits']['hits'])
        return results

    def filter_records(self, results, ids):
        """Filter records by ids.

        :param results: dictionary with the results in hits hits
        :param ids: list with ids to filter
        :returns: dictionary with results filtered by ids and
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
        :returns: list of ids
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

    def search_records(self, what, relation, where='anywhere', max=0):
        """Get the records.

        :param what: what term to search
        :param relation: relation for what and where
        :param where: in witch index to search
        """
        if max == 0:
            max = self.max
        self.init_results()
        if not what:
            return self.results, 200
        try:
            cache_key = '{what}_{relation}_{where}_{max}'.format(
                what=what,
                relation=relation,
                where=where,
                max=max
            )
            cache = self.cache.get(cache_key)
            if cache:
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
                with requests.get(url_api) as response:
                    if not response.ok:
                        self.status_code = 502
                        response = {
                            'metadata': {},
                            'errors': {
                                'code': self.status_code,
                                'title': '{name}: Bad status code!'.format(
                                    name=self.name
                                ),
                                'detail': 'Status code: {code}'.format(
                                    code=response.status_code
                                )
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
                            record = unimarc.do(json_data)
                            id = self.get_id(json_data)
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
                        self.results['hits']['remote_total'] = int(etree.parse(
                                BytesIO(response.content))
                                .find('{*}numberOfRecords').text)
            self.results['hits']['total'] = len(self.results['hits']['hits'])
            if self.results['hits']['total'] == 0:
                self.status_code = 404
                self.results['errors'] = {
                    'code': self.status_code,
                    'title': ('{name}: Not found: '
                              '{where} {relation} {what}').format(
                                name=self.name,
                                where=where,
                                relation=relation,
                                what=what
                              )
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

        # other errors
        except Exception as error:
            current_app.logger.error(
                '{title}: {detail}'.format(
                    title='{name} Error!'.format(name=self.name),
                    detail='Error: {error}'.format(error=error)
                )
            )
            abort(500, description='Error: {error}'.format(error=error))
        return self.results, self.status_code


class BnfImport(Import):
    """Import class for BNF."""

    name = 'BNF'
    url = 'http://catalogue.bnf.fr'
    url_api = '{url}/api/SRU?'\
              'version=1.2&operation=searchRetrieve'\
              '&recordSchema=unimarcxchange&maximumRecords={max}'\
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

    marc_to_json = unimarc

    def get_marc21_link(self, id):
        """Get direct link to marc21 record.

        :param id: id to use for the link
        :returns: url for id
        """
        args = {
            'id': id,
            '_external': True,
            current_app.config.get(
                'REST_MIMETYPE_QUERY_ARG_NAME', 'format'): 'marc'
        }
        return url_for('api_imports.imports_record', **args)
