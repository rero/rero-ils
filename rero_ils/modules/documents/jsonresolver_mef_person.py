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

"""Mef Person resolver."""

import jsonresolver
from flask import current_app
from requests import codes as requests_codes
from requests import get as requests_get


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


# TODO: dynamic route for host configuration in config.py
@jsonresolver.route('/api/mef/<pid>', host='mef.rero.ch')
def mef_person_resolver(pid):
    """MEF person resolver."""
    mef_url = '{url}/mef/{pid}'.format(
        url=current_app.config.get('RERO_ILS_MEF_URL'),
        pid=pid
    )
    if mef_url:
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
                # name
                name = get_mef_value(data, 'preferred_name_for_person')
                if name:
                    author['name'] = name
                    # date
                    date_of_birth = get_mef_value(
                        data,
                        'date_of_birth',
                        ''
                    )
                    date_of_death = get_mef_value(
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
