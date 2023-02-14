# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLouvain
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

"""Documents dumpers."""

from invenio_records.dumpers import Dumper

from rero_ils.modules.commons.dumpers import MultiDumper

from .indexer import IndexerDumper
from .replace_refs import ReplaceRefsContributionsDumper, ReplaceRefsDumper, \
    ReplaceRefsSubjectsDumper
from .title import TitleDumper

__all__ = (
    'TitleDumper',
    'ReplaceRefsContributionsDumper',
    'ReplaceRefsSubjectsDumper',
    'ReplaceRefsDumper'
)

# replace linked data
document_replace_refs = MultiDumper(dumpers=[
    # make a fresh copy
    Dumper(),
    ReplaceRefsContributionsDumper(),
    ReplaceRefsSubjectsDumper(),
    ReplaceRefsDumper()
])

# create a string version of the complex title field
document_title = MultiDumper(dumpers=[
    # make a fresh copy
    Dumper(),
    TitleDumper()
])

# dumper used for indexing
document_indexer = MultiDumper(dumpers=[
    # make a fresh copy
    Dumper(),
    ReplaceRefsContributionsDumper(),
    ReplaceRefsSubjectsDumper(),
    ReplaceRefsDumper(),
    IndexerDumper()
])
