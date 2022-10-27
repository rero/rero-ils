# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
# Copyright (C) 2019-2022 UCLOUVAIN
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

"""MARC21 RERO to JSON."""

from .dnb.model import marc21 as marc21_dnb
from .kul.model import marc21 as marc21_kul
from .loc.model import marc21 as marc21_loc
from .rero.model import marc21 as marc21_rero
from .slsp.model import marc21 as marc21_slsp
from .ugent.model import marc21 as marc21_ugent

__all__ = ('marc21_dnb', 'marc21_kul', 'marc21_loc', 'marc21_rero',
           'marc21_slsp', 'marc21_ugent')
