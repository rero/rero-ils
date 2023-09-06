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

"""Remote entity proxies."""
import json
from urllib.parse import quote_plus

import requests
from flask import abort, current_app, jsonify, request

from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.utils import get_mef_url


class MEFProxyFactory:
    """MEF proxy factory.

    Depending on the entity category we are searching, we need to use a
    specific proxy class. This is the purpose of the factory : it will check
    this category and return an instance of the correct proxy class to use.
    We just need to run a search on some terms on this proxy instance to get
    remote MEF authority server response.

    USAGE:
        >> proxy = MEFProxyFactory.create_proxy('agents')
        >> proxy.search('my_search_term')
    """

    @staticmethod
    def create_proxy(category):
        """The concrete factory method.

        :param category: the search category ('agents', 'organisation', ...)
        :returns: a concrete instance of proxy to use for searching.
        :raises ValueError: if no proxy instance can be created.
        """
        # Create the proxy configuration mapping table. For each entry in this
        # dictionary, we need to specify 2 keys :
        #   - 'class': the concrete `MEFProxy` class to use
        #   - 'entities':
        # DEV NOTES :: `agents` isn't yet used, but could be ASAP. This is why
        #              it's already configured.
        proxy_config = {
            'agents': {
                'class': MefAgentsProxy,
                'entities': (EntityType.PERSON, EntityType.ORGANISATION)
            },
            'person': {
                'class': MefAgentsProxy,
                'entities': (EntityType.PERSON,)
            },
            'organisation': {
                'class': MefAgentsProxy,
                'entities': (EntityType.ORGANISATION,)
            },
            'concepts': {
                'class': MefConceptsProxy,
                'entities': (EntityType.TOPIC, EntityType.TEMPORAL)
            },
            'topics': {
                'class': MefConceptsProxy,
                'entities': (EntityType.TOPIC,)
            },
            'temporals': {
                'class': MefConceptsProxy,
                'entities': (EntityType.TEMPORAL, )
            },
            'concepts-genreForm': {
                'class': MefConceptsGenreFormProxy,
                'entities': (EntityType.TOPIC,)
            },
            'places': {
                'class': MefPlacesProxy,
                'entities': (EntityType.PLACE, )
            },
        }
        # Create proxy configuration aliases
        proxy_config[EntityType.PERSON] = proxy_config['person']
        proxy_config[EntityType.ORGANISATION] = proxy_config['organisation']
        proxy_config[EntityType.TOPIC] = proxy_config['topics']
        proxy_config[EntityType.TEMPORAL] = proxy_config['temporals']
        proxy_config[EntityType.PLACE] = proxy_config['places']

        # Try to create the proxy, otherwise raise a ValueError
        if data := proxy_config.get(category):
            return data['class'](*(data['entities']))
        raise ValueError(f'Unable to find a MEF factory for {category}')


class MEFProxyMixin:
    """Proxy on RERO-MEF authority system.

    This is a ``Mixin`` class : It can't be used a concrete class to avoid any
    `NotImplementedError` exception.

    A MEF proxy is used to search authority entries on a remove MEF server.
    This mixin class define basic behavior to search a term and return the
    response where hits are cleaned/formatted.

    Create a subclass inherits of this Mixin and override methods :
      - `_get_query_params`: to get all params to use for the MEF query.
      - `_post_process_result_hit`: to clean/format each MEF hit response.
    """

    # Headers that should be excluded from remote MEF system response.
    excluded_headers = [
        'Content-Encoding',
        'Content-Length',
        'Transfer-Encoding',
        'Connection'
    ]
    mef_entrypoint = None  # Must be overridden by subclasses

    def __init__(self, *args):
        """Magic initialization method."""
        self.entity_types = args
        self.sources = current_app.config \
            .get('RERO_ILS_MEF_CONFIG', {}) \
            .get(self.mef_entrypoint, {}) \
            .get('sources', [])
        self.filters = current_app.config \
            .get('RERO_ILS_MEF_CONFIG', {}) \
            .get(self.mef_entrypoint, {}) \
            .get('filters', [])

    def search(self, term):
        """Search specific term on MEF authority system.

        :param term: the searched term.
        :type term: str
        :returns: the remote MEF response matching the search term
        :rtype: flask.Response
        """
        # Call the remote MEF server removing the 'Host' headers from initial
        # request to avoid security problems.
        request_headers = {
            key: value
            for key, value in request.headers
            if key != 'Host'
        }
        response = requests.request(
            method=request.method,
            url=self._build_url(term),
            headers=request_headers,
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=True
        )

        # If remote server response failed, raise this HTTP error through a
        # valid flask `abort` response.
        if response.status_code != requests.codes.ok:
            abort(response.status_code)

        # Post-process the result hits to get a standard format against all
        # format possibility depending on entity type searched.
        content = json.loads(response.content)
        for hit in content.get('hits', {}).get('hits', []):
            self._post_process_result_hit(hit)

        # Finally, return a flask `Response` from a `request.Response`. All
        # remote server response headers were cloned in the new response except
        # some inconsistent headers.
        flask_response = jsonify(content)
        for header_name, header_value in response.headers.items():
            if header_name not in self.excluded_headers:
                flask_response.headers[header_name] = header_value
        return flask_response

    def _get_query_params(self, term):
        """Get all parameters to use to build the MEF query.

        :param term: the searched term
        :type term: str
        :returns: a list of query parameters to build the `q` parameter to send
           to the remote MEF server to filter the response. All these params
           will be joined by 'AND' condition.
        :rtype: list<str>
        """

        def _build_filter_value(value):
            if isinstance(value, list):
                return f'({" OR ".join(value)})'
            return f'"{str(value)}"'

        query_params = [f'((autocomplete_name:{term})^2 OR {term})']
        if self.sources:
            query_params.append(f'sources:{_build_filter_value(self.sources)}')
        for filter_field in self.filters:
            for key, value in filter_field.items():
                filter_value = _build_filter_value(value)
                query_params.append(f'{key}:{filter_value}')
        return query_params

    def _build_url(self, term):
        """Build the HTTP query to call to search on MEF authority system.

        :param term: the searched term.
        :type term: str
        :returns: the MEF URL to call to get response hits.
        :rtype: str
        """
        query = quote_plus(' AND '.join(self._get_query_params(term)))
        base_url = get_mef_url(self.mef_entrypoint)
        return f'{base_url}/mef?q={query}&page=1&size=10&facets='

    def _post_process_result_hit(self, hit):
        """Modify a MEF hit response to return a standardized hit."""
        # We would like to add the direct MEF URI for each source of the hit.
        # This URI is the direct access for the source metadata on the remote
        # MEF authority server.
        # TODO :: this URI should be returned by MEF API
        if not (metadata := hit.get('metadata')):
            return
        base_url = get_mef_url(self.mef_entrypoint)
        for source_name in self.sources:
            if not (src_data := metadata.get(source_name)):
                continue
            src_data.setdefault('identifiedBy', []).append({
                'source': 'mef',
                'type': 'uri',
                'value': f'{base_url}/{source_name}/{src_data["pid"]}'
            })


class MefAgentsProxy(MEFProxyMixin):
    """Proxy on RERO-MEF authority system when searching for `agents`."""

    mef_entrypoint = 'agents'

    def _get_query_params(self, term):
        """Get all parameters to use to build the MEF query.

        :param term: the searched term
        :type term: str
        :returns: a list of query parameters to build the `q` parameter to send
           to the remote MEF server to filter the response. All these params
           will be joined by 'AND' condition.
        :rtype: list<str>
        """
        params = super()._get_query_params(term)
        if self.entity_types:
            ent_types = []
            for _type in self.entity_types:
                _type = _type.replace(":", "\\:")
                ent_types.append(f'type:{_type}')
            params += [f'({" OR ".join(ent_types)})']
        return params

    def _post_process_result_hit(self, hit):
        """Modify a MEF hit response to return a standardized hit.

        The modification to do on an 'Agent' hit are :
          - for each used sources: (TODO :: Need MEF correction)
            - rebuild an "identifiedBy" array based on "identifier" field.

        :param hit: an elasticSearch hit already parsed as a dictionary.
        """
        if not (metadata := hit.get('metadata', {})):
            return
        for source_name in self.sources:
            if not (src_data := metadata.get(source_name)):
                continue
            if identifier := src_data.pop('identifier', None):
                src_data.setdefault('identifiedBy', []).append({
                    'source': source_name,
                    'type': 'uri',
                    'value': identifier
                })
        super()._post_process_result_hit(hit)


class MefConceptsProxy(MEFProxyMixin):
    """Proxy on RERO-MEF authority system when searching for `concepts`."""

    mef_entrypoint = 'concepts'

    def _get_query_params(self, term):
        """Get all parameters to use to build the MEF query.

        :param term: the searched term
        :type term: str
        :returns: a list of query parameters to build the `q` parameter to send
           to the remote MEF server to filter the response. All these params
           will be joined by 'AND' condition.
        :rtype: list<str>
        """
        params = super()._get_query_params(term)
        if self.entity_types:
            ent_types = []
            for _type in self.entity_types:
                _type = _type.replace(":", "\\:")
                ent_types.append(f'type:{_type}')
            params += [f'({" OR ".join(ent_types)})']
        return params

    def _post_process_result_hit(self, hit):
        """Modify a MEF hit response to return a standardized hit.

        The modification to do on an 'Agent' hit are :
          - for each used sources: (TODO :: Need MEF correction)
            - add a `type` field

        :param hit: an elasticSearch hit already parsed as a dictionary.
        """
        if not (metadata := hit.get('metadata', {})):
            return
        super()._post_process_result_hit(hit)


class MefConceptsGenreFormProxy(MefConceptsProxy):
    """Proxy on RERO-MEF authority system for specific `genreForm` concepts."""

    mef_entrypoint = 'concepts-genreForm'


class MefPlacesProxy(MEFProxyMixin):
    """Proxy on RERO-MEF authority system when searching for `places`."""

    mef_entrypoint = 'places'
