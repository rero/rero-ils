# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2023 RERO
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

"""Message interface."""

from invenio_cache.proxies import current_cache
from markupsafe import Markup


class Message():
    """Message for the user."""

    prefix = 'message_'

    @classmethod
    def set(cls, key, type, value):
        """Set value.

        :param key: the cache key.
        :param type: the type of message.
        :param value: the value of message.
        :return: True if the insertion went well.
        """
        data = {'type': type or 'primary', 'message': Markup(value)}
        return current_cache.set(f'{cls.prefix}{key}', data)

    @classmethod
    def get(cls, key):
        """Get value.

        :param key: the cache key.
        :return: empty or the json.
        """
        return current_cache.get(f'{cls.prefix}{key}')

    @classmethod
    def delete(cls, key):
        """Delete value.

        :param key: the cache key.
        :return: True if the removal went well.
        """
        return current_cache.delete(f'{cls.prefix}{key}')
