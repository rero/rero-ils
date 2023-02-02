# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2022 RERO
# Copyright (C) 2022 UCLouvain
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

"""Document record extensions."""
from .add_mef_pid import AddMEFPidExtension
from .edition_statement import EditionStatementExtension
from .provision_activities import ProvisionActivitiesExtension
from .series_statement import SeriesStatementExtension
from .title import TitleExtension

__all__ = (
    'AddMEFPidExtension',
    'ProvisionActivitiesExtension',
    'SeriesStatementExtension',
    'EditionStatementExtension',
    'TitleExtension'
)
