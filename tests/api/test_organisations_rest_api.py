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


def test_location_can_delete(client, organisation, library):
    """Test can delete an organisation."""
    links = organisation.get_links_to_me()
    assert 'libraries' in links

    assert not organisation.can_delete

    reasons = organisation.reasons_not_to_delete()
    assert 'links' in reasons
