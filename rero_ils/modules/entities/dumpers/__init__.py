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

"""Common entity dumpers."""
from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.dumpers import MultiDumper, ReplaceRefsDumper

from .authorized_acces_point import LocalizedAuthorizedAccessPointDumper
from .document import BaseDocumentEntityDumper
from .indexer import EntityIndexerDumper

# replace linked data (seems not necessary at this time)
replace_refs_dumper = MultiDumper(dumpers=[
    # make a fresh copy
    Dumper(),
    ReplaceRefsDumper()
])

# dumper used for indexing
indexer_dumper = MultiDumper(dumpers=[
    # make a fresh copy
    Dumper(),
    ReplaceRefsDumper(),
    EntityIndexerDumper(),
    LocalizedAuthorizedAccessPointDumper()
])

document_dumper = MultiDumper(dumpers=[
    BaseDocumentEntityDumper(),
    EntityIndexerDumper(),
    LocalizedAuthorizedAccessPointDumper(),
])
