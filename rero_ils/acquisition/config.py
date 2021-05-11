# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2021 RERO
# Copyright (C) 2021 UCLouvain
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

"""Default configuration for RERO ILS acquisitions."""

ACQ_RECORDS_RESOURCES = dict()
"""Default Records resources loaded.

This option can be overwritten to describe the resource of different
resource types.

The structure of the dictionary is as follows:
.. code-block:: python

    from invenio_records_resources.resources import RecordResource, \
        RecordResourceConfig
    from invenio_records_resources.services import RecordService, \
        RecordServiceConfig

    ACQ_RECORDS_RESOURCES = dict(
        my_resources = RecordResource(
            config=RecordResourceConfig,
            service=RecordService(RecordServiceConfig)
        )
    )
"""
