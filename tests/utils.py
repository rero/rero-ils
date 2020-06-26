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

"""Tests Utils."""


import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session, \
    login_user_via_view
from invenio_circulation.api import get_loan_for_item
from invenio_search import current_search
from six.moves.urllib.parse import parse_qs, urlparse

from rero_ils.modules.circ_policies.api import CircPolicy
from rero_ils.modules.documents.api import Document
from rero_ils.modules.holdings.api import Holding
from rero_ils.modules.item_types.api import ItemType
from rero_ils.modules.items.api import Item
from rero_ils.modules.items.utils import item_pid_to_object
from rero_ils.modules.libraries.api import Library
from rero_ils.modules.locations.api import Location
from rero_ils.modules.organisations.api import Organisation
from rero_ils.modules.patron_types.api import PatronType
from rero_ils.modules.patrons.api import Patron


class VerifyRecordPermissionPatch(object):
    """Verify record permissions."""

    status_code = 200


def login_user(client, user):
    """Sign in user."""
    user.user.password_plaintext = user.get('email')
    login_user_via_session(client, user=user.user)


def login_user_for_view(client, user):
    """Sign in user for view."""
    user.user.password_plaintext = user.get('email')
    login_user_via_view(client, user=user.user)


def get_json(response):
    """Get JSON from response."""
    return json.loads(response.get_data(as_text=True))


def postdata(client, endpoint, data=None, headers=None, url_data=None):
    """
    Build URL from given endpoint and send given data to it.

    Returns result and JSON from result.
    """
    if data is None:
        data = {}
    if headers is None:
        headers = [
            ('Accept', 'application/json'),
            ('Content-Type', 'application/json')
        ]
    if url_data is None:
        url_data = {}
    res = client.post(
        url_for(endpoint, **url_data),
        data=json.dumps(data),
        content_type='application/json',
        headers=headers
    )
    output = get_json(res)
    return res, output


def to_relative_url(url):
    """Build relative URL from external URL.

    This is needed because the test client discards query parameters on
    external urls.
    """
    parsed = urlparse(url)
    return parsed.path + '?' + '&'.join([
        '{0}={1}'.format(param, val[0]) for
        param, val in parse_qs(parsed.query).items()
    ])


def get_mapping(name):
    """Returns es mapping."""
    return current_search.client.indices.get_mapping(name)


def flush_index(name):
    """Flush index."""
    return current_search.flush_and_refresh(name)


def loaded_resources_report():
    """For debug only: returns a list or count of loaded objects."""
    objects = {
        'organisations': Organisation,
        'libraries': Library,
        'locations': Location,
        'circ_policies': CircPolicy,
        'item_types': ItemType,
        'patron_types': PatronType,
        'patrons': Patron,
        'documents': Document,
        'items': Item,
        'holdings': Holding
    }
    report = {}
    for object in objects:
        object_pids = objects[object].get_all_pids()
        report[object] = len(list(object_pids))
        item_details = []
        if object == 'items':
            for item in object_pids:
                item_details.append(
                    {
                        'item_pid': item,
                        'item_status': objects[object].get_record_by_pid(
                            item).status,
                        'requests': objects[object].get_record_by_pid(
                            item).number_of_requests(),
                        'loans': get_loan_for_item(item_pid_to_object(item))
                    }
                )
        report['item_details'] = item_details
    return report


def mock_response(status=200, content="CONTENT", json_data=None,
                  raise_for_status=None):
    """Mock a request response."""
    mock_resp = mock.Mock()
    # mock raise_for_status call w/optional error
    mock_resp.raise_for_status = mock.Mock()
    if raise_for_status:
        mock_resp.raise_for_status.side_effect = raise_for_status
    # set status code and content
    mock_resp.status_code = status
    mock_resp.content = content
    # add json data if provided
    if json_data:
        mock_resp.json = mock.Mock(return_value=json_data)
    return mock_resp


def get_timezone_difference(timezone, date):
    """Get timezone offset difference, in hours."""
    if date.tzinfo is not None:
        date = date.replace(tzinfo=None)
    return int(timezone.utcoffset(date).total_seconds()/3600)


def check_timezone_date(timezone, date, expected=[]):
    """Check hour and minute of given date regarding given timezone."""
    difference = get_timezone_difference(timezone, date)
    # In case the difference is positive, the result hour could be greater
    # or equal to 24.
    # A day doesn't contain more than 24 hours.
    # We so use modulo to always have less than 24.
    hour = (date.hour + difference) % 24
    # Prepare date
    tocheck_date = date.astimezone(timezone)
    error_msg = "Date: %s. Expected: %s. Minutes should be: %s. Hour: %s" % (
        tocheck_date, date, date.minute, hour)
    # Expected list defines accepted hours for tests
    if expected:
        assert hour in expected, error_msg
    assert tocheck_date.minute == date.minute, error_msg
    assert tocheck_date.hour == hour, error_msg
