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

"""Common exceptions for RERO-ILS resources."""


class RecordNotFound(Exception):
    """Record con't be found into Invenio."""

    def __init__(self, record_cls, record_pid):
        """Initialization method.

        :param record_cls: (IlsRecord) the resource class.
        :param record_pid: (string) the resource pid.
        """
        self.record_cls = record_cls
        self.record_pid = record_pid

    def __str__(self):
        """String representation of the exception."""
        return f'{self.record_cls.__name__}#{self.record_pid} not found'
