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

"""Mef Person resolver."""

import jsonresolver
from flask import current_app
from requests import codes as requests_codes
from requests import get as requests_get

from rero_ils.utils import unique_list


# TODO: if I delete the id the mock is not working any more ????
def get_mef_value(data, key, default=None):
    """Get the data for key rero -> bnf -> gnd."""
    value = None
    sources = current_app.config.get('RERO_ILS_PERSONS_SOURCES', [])
    for source in sources:
        value = data.get(source, {}).get(key, default)
        if value:
            return value
    return value


def localized_data(data, key, language):
    """Get localized data."""
    order = current_app.config.get('RERO_ILS_PERSONS_LABEL_ORDER', [])
    source_order = order.get(language, order.get(order['fallback'], []))
    for source in source_order:
        value = data.get(source, {}).get(key, None)
        if value:
            return value
    return data.get(key, None)


def get_defined_languages():
    """Get defined languages from config."""
    languages = [current_app.config.get('BABEL_DEFAULT_LANGUAGE')]
    i18n_languages = current_app.config.get('I18N_LANGUAGES')
    return languages + [ln[0] for ln in i18n_languages]


# TODO: dynamic route for host configuration in config.py
@jsonresolver.route('/api/mef/<pid>', host='mef.rero.ch')
def mef_person_resolver(pid):
    """MEF person resolver."""
    mef_url = '{url}{pid}'.format(
        url=current_app.config.get('RERO_ILS_MEF_URL'),
        pid=pid
    )

    request = requests_get(url=mef_url, params=dict(
        resolve=1,
        sources=1
    ))
    if request.status_code == requests_codes.ok:
        data = request.json().get('metadata')
        if data:
            author = {
                'type': 'person',
                'pid': pid
            }
            for language in get_defined_languages():
                author[
                    'name_{language}'.format(language=language)
                ] = localized_data(
                    data, 'preferred_name_for_person', language
                )
            # date
            date_of_birth = get_mef_value(data, 'date_of_birth', '')
            date_of_death = get_mef_value(data, 'date_of_death', '')
            if date_of_birth or date_of_death:
                date = '{date_of_birth}-{date_of_death}'.format(
                    date_of_birth=date_of_birth,
                    date_of_death=date_of_death
                )
                author['date'] = date
            # variant_name
            variant_person = []
            for source in data['sources']:
                if 'variant_name_for_person' in data[source]:
                    variant_person = variant_person +\
                        data[source]['variant_name_for_person']
            if variant_person:
                author['variant_name'] = unique_list(variant_person)
            return author
        else:
            current_app.logger.error(
                'Mef resolver no metadata: {result} {url}'.format(
                    result=request.json(),
                    url=mef_url
                )
            )
    else:
        current_app.logger.error(
            'Mef resolver request error: {result} {url}'.format(
                result=request.status_code,
                url=mef_url
            )
        )
        raise Exception('unable to resolve')
