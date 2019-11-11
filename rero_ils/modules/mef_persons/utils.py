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

"""Utilities for mef persons."""

from flask import current_app
from requests import codes as requests_codes
from requests import get as requests_get


def resolve_mef(mef_uri):
    """Resolve mef reference.

    :param mef_uri : uri to resolve
    :return data from MEF
    """
    mef_uri.replace(
        'mef.rero.ch',
        current_app.config['RERO_ILS_MEF_HOST']
    )
    r = requests_get(
        url=mef_uri,
        params={
            'resolve': 1,
            'sources': 1
        })

    if r.status_code == requests_codes.ok:
        data = r.json()
        return data if data.get('id') else None
