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

from flask import current_app
from flask_caching.backends import RedisCache
from invenio_cache.proxies import current_cache
from markupsafe import Markup
from redis import Redis


class Message:
    """Message for the user."""

    prefix = "message_"

    @classmethod
    def set(cls, key, type, value, timeout=0):
        """Set value.

        :param key: the cache key.
        :param type: the type of message.
        :param value: the value of message.
        :return: True if the insertion went well.
        """
        data = {"type": type or "primary", "message": Markup(value)}
        return current_cache.set(f"{cls.prefix}{key}", data, timeout=0)

    @classmethod
    def get(cls, key):
        """Get value.

        :param key: the cache key.
        :return: empty or the json.
        """
        return current_cache.get(f"{cls.prefix}{key}")

    @classmethod
    def delete(cls, key):
        """Delete value.

        :param key: the cache key.
        :return: True if the removal went well.
        """
        return current_cache.delete(f"{cls.prefix}{key}")

    @classmethod
    def get_all_messages(cls):
        """Get All Messages."""
        messages = {}
        if isinstance(current_cache.cache, RedisCache):
            # current_cache for REDIS has no function to get all values. Get them directly from REDIS.
            if url := current_app.config.get("CACHE_REDIS_URL"):
                redis = Redis.from_url(url)
                redis_keys = [
                    redis_key.decode("utf-8").replace(f"cache::{cls.prefix}", "")
                    for redis_key in redis.scan_iter(f"cache::{cls.prefix}*")
                ]
                for key in redis_keys:
                    messages[key] = cls.get(key)
        else:
            # needed for tests
            messages = {
                key.replace(f"{cls.prefix}", ""): current_cache.get(key)
                for key in current_cache.cache._cache
            }

        return messages
