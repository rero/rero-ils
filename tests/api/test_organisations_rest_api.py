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

"""Tests REST API organisations."""

import json

import mock
from flask import url_for
from invenio_accounts.testutils import login_user_via_session
from utils import VerifyRecordPermissionPatch, get_json, to_relative_url


def test_location_can_delete(client, org_martigny, lib_martigny):
    """Test can delete an organisation."""
    links = org_martigny.get_links_to_me()
    assert 'libraries' in links

    assert not org_martigny.can_delete

    reasons = org_martigny.reasons_not_to_delete()
    assert 'links' in reasons


def test_organisation_secure_api(client, json_header, org_martigny,
                                 librarian_martigny_no_email,
                                 librarian_sion_no_email):
    """Test organisation secure api access."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.org_item',
                         pid_value=org_martigny.pid)

    res = client.get(record_url)
    assert res.status_code == 200

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)
    record_url = url_for('invenio_records_rest.org_item',
                         pid_value=org_martigny.pid)


def test_organisation_secure_api_create(client, json_header, org_martigny,
                                        librarian_martigny_no_email,
                                        librarian_sion_no_email,
                                        org_martigny_data):
    """Test organisation secure api create."""
    # Martigny
    login_user_via_session(client, librarian_martigny_no_email.user)
    post_url = url_for('invenio_records_rest.org_list')

    del org_martigny_data['pid']
    res = client.post(
        post_url,
        data=json.dumps(org_martigny_data),
        headers=json_header
    )
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.post(
        post_url,
        data=json.dumps(org_martigny_data),
        headers=json_header
    )
    assert res.status_code == 403


def test_organisation_secure_api_update(client, json_header, org_martigny,
                                        librarian_martigny_no_email,
                                        librarian_sion_no_email,
                                        org_martigny_data):
    """Test organisation secure api create."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.org_item',
                         pid_value=org_martigny.pid)

    data = org_martigny_data
    data['name'] = 'New Name'
    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.put(
        record_url,
        data=json.dumps(data),
        headers=json_header
    )
    assert res.status_code == 403


def test_organisation_secure_api_delete(client, json_header, org_martigny,
                                        librarian_martigny_no_email,
                                        librarian_sion_no_email,
                                        org_martigny_data):
    """Test organisation secure api delete."""
    login_user_via_session(client, librarian_martigny_no_email.user)
    record_url = url_for('invenio_records_rest.org_item',
                         pid_value=org_martigny.pid)

    res = client.delete(record_url)
    assert res.status_code == 403

    # Sion
    login_user_via_session(client, librarian_sion_no_email.user)

    res = client.delete(record_url)
    assert res.status_code == 403
