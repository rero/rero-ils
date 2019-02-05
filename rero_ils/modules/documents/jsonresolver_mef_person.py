# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Organisation resolver."""


import jsonresolver
import requests
from flask import current_app


def get_mef_value(data, key, default=None):
    """Get the data for key rero -> bnf -> gnd."""
    id = {}
    value = data.get('rero', {}).get(key, default)
    if not value:
        value = data.get('bnf', {}).get(key, default)
        if not value:
            value = data.get('gnd', {}).get(key, default)
            if value:
                id['gndID'] = data['gnd']['pid']
        else:
            id['bnfID'] = data['bnf']['pid']
    else:
        id['reroID'] = data['rero']['pid']
    return value, id


@jsonresolver.route('/api/mef/<pid>', host='mef.test.rero.ch')
def mef_person_resolver(pid):
    """MEF person resolver."""
    mef_url = current_app.config.get(
        'RERO_ILS_MEF_URL'
    ) + '/mef/' + pid
    if mef_url:
        request = requests.get(url=mef_url, params=dict(resolve=1))
        if request.status_code == requests.codes.ok:
            data = request.json().get('metadata')
            if data:
                author = {}
                author['Identifiers'] = {}
                # name
                name, id = get_mef_value(data, 'preferred_name_for_person')
                id['mefID'] = pid
                if name:
                    author['name'] = name
                    author['Identifiers'] = id
                    # date
                    date_of_birth, id = get_mef_value(
                        data,
                        'date_of_birth',
                        ''
                    )
                    date_of_death, id = get_mef_value(
                        data,
                        'date_of_death',
                        ''
                    )
                    if date_of_birth or date_of_death:
                        date = '{date_of_birth}-{date_of_death}'.format(
                            date_of_birth=date_of_birth,
                            date_of_death=date_of_death
                        )
                        author['date'] = date
                    # qualifier ?????
                    return author
                else:
                    current_app.logger.error(
                        'Mef resolver no name: {result} {url}'.format(
                            result=data,
                            url=mef_url
                        )
                    )
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
