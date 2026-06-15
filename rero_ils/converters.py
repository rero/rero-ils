# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-FileCopyrightText: UCLouvain
# SPDX-License-Identifier: AGPL-3.0-or-later

"""General converters utilities module."""

from invenio_records_rest.utils import PIDConverter
from werkzeug.utils import cached_property


class NoopPIDValue:
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
