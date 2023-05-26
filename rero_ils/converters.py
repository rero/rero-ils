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

"""General converters utilities module."""
from invenio_records_rest.utils import PIDConverter
from werkzeug.utils import cached_property


class NoopPIDValue(object):
    """Noop PID resolver class."""

    def __init__(self, value):
        """Initialize with the PID value.

        :params value: PID value.
        :type value: str
        """
        self.value = value

    @cached_property
    def data(self):
        """Resolve PID from a value.

        :returns: A tuple with the PID and an empty record.
        """
        return self.value, {}


class NoopPIDConverter(PIDConverter):
    """Converter for PID values in the route mapping.

    This class is a custom routing converter defining the 'PID' type.
    See http://werkzeug.pocoo.org/docs/0.12/routing/#custom-converters.

    Use ``pid`` as a type in the route pattern, e.g.: the use of
    route decorator: ``@blueprint.route('/record/<pid(recid):pid_value>')``,
    will match and resolve a path: ``/record/123456``.
    """

    def to_python(self, value):
        """Resolve PID value."""
        return NoopPIDValue(value)
