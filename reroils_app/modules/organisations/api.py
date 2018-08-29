# -*- coding: utf-8 -*-
#
# This file is part of REROILS.
# Copyright (C) 2017 RERO.
#
# REROILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# REROILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with REROILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""API for manipulating organisation."""


from ..api import IlsRecord
from .fetchers import organisation_id_fetcher
from .minters import organisation_id_minter
from .providers import OrganisationProvider


class Organisation(IlsRecord):
    """Organisation class."""

    minter = organisation_id_minter
    fetcher = organisation_id_fetcher
    provider = OrganisationProvider
