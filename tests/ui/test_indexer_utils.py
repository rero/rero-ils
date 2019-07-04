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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""API tests for indexer utilities."""

from rero_ils.modules.indexer_utils import record_to_index


def test_record_to_index(app):
    """Test the index name value from the JSONSchema."""

    # for documents
    assert record_to_index({
        '$schema': 'https://ils.rero.ch/schema/'
        'documents/document-minimal-v0.0.1.json'
    }) == ('documents-document', 'document')

    # for others
    assert record_to_index({
        '$schema': 'https://ils.rero.ch/schema/'
        'organisations/organisation-v0.0.1.json'
    }) == ('organisations-organisation-v0.0.1', 'organisation-v0.0.1')
