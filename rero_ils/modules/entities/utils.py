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

"""Entities utilities."""

from __future__ import absolute_import, print_function

from flask import current_app
from requests import RequestException
from requests import codes as requests_codes

from rero_ils.modules.entities.models import EntityType
from rero_ils.modules.utils import get_mef_url, requests_retry_session


def get_entity_localized_value(entity, key, language):
    """Get the first localized value for given key among MEF source list.

    :param entity: Entity data.
    :param key: Key to find a translated form.
    :param language: Language to use.
    :returns: Value from key in language if found otherwise the value of key.
    """
    order = current_app.config.get('RERO_ILS_AGENTS_LABEL_ORDER', [])
    source_order = order.get(language, order.get(order['fallback'], []))
    for source in source_order:
        if value := entity.get(source, {}).get(key):
            return value
    return entity.get(key)


def extract_data_from_mef_uri(mef_uri):
    """Extract agent type and pid form the MEF URL.

    :params mef_uri: MEF URI.
    :returns: the entity_type, the ref type such as idref, and the pid value.
    :rtype tuple
    """
    ref_split = mef_uri.split('/')
    # TODO :: check back compatibility
    return ref_split[-3], ref_split[-2], ref_split[-1]


def remove_schema(data):
    """Removes in place the $schema values.

    Removes the root and the sources $schema.

    :param data: the data representation of the current contribution as a dict.
    :returns: the modified data.
    :rtype: dict.
    """
    data.pop('$schema', None)
    for source in current_app.config.get('RERO_ILS_AGENTS_SOURCES', []):
        if source in data:
            data[source].pop('$schema', None)
    return data


def get_mef_data_by_type(pid_type, pid, entity_type='agents', verbose=False,
                         with_deleted=True, resolve=True, sources=True):
    """Request MEF REST API in JSON format.

    :param pid_type: the type of entity (idref, gnd, viaf, ...)
    :param pid: the entity pid into authority source
    :param entity_type: the entity type
    :param verbose: is messages should be logged
    :param with_deleted: is the deleted entity should be search for.
    :param resolve: is references should be resolved from source
    :param sources: is sources should be included into response.
    :returns: corresponding entity metadata from authority server
    :rtype dict
    """
    # Depending on the entity type, try to get the correct MEF base URL.
    # If no base URL could be found, a key error will be raised
    if not (base_url := get_mef_url(entity_type)):
        msg = f'Unable to find MEF base url for {entity_type}'
        if verbose:
            current_app.logger.warning(msg)
        raise KeyError(msg)

    if pid_type == 'mef':
        mef_url = f'{base_url}/mef/?q=pid:"{pid}"'
    elif pid_type == 'viaf':
        mef_url = f'{base_url}/mef/?q=viaf_pid:"{pid}"'
    else:
        mef_url = f'{base_url}/mef/latest/{pid_type}:{pid}'

    request = requests_retry_session().get(url=mef_url, params={
        'with_deleted': int(with_deleted),
        'resolve': int(resolve),
        'sources': int(sources)
    })
    if request.status_code == requests_codes.ok:
        try:
            json_data = request.json()
            if hits := json_data.get('hits', {}):
                # we got an ES response
                data = hits.get('hits', [None])[0].get('metadata', {})
            else:
                # we got an DB response
                data = json_data
                data.pop('_created', None)
                data.pop('_updated', None)

            # TODO :: This `if` statement should be removed when MEF will
            #         return the `type` key for concept
            if entity_type == 'concepts':
                data.setdefault('type', EntityType.TOPIC)

            return remove_schema(data)
        except Exception as err:
            msg = f'MEF resolver no metadata: {mef_url} {err}'
            if verbose:
                current_app.logger.warning(msg)
            raise ValueError(msg) from err
    else:
        msg = f'Mef http error: {request.status_code} {mef_url}'
        if verbose:
            current_app.logger.error(msg)
        raise RequestException(msg)
