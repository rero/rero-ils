# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Message interface."""

from flask_caching.backends import RedisCache
from invenio_cache.proxies import current_cache
from markupsafe import Markup


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
            # current_cache has no API to scan keys; use the underlying client directly.
            full_prefix = f"{current_cache.cache._get_prefix()}{cls.prefix}"
            for redis_key in current_cache.cache._write_client.scan_iter(f"{full_prefix}*"):
                key_str = redis_key.decode("utf-8") if isinstance(redis_key, bytes) else redis_key
                msg_key = key_str.removeprefix(full_prefix)
                messages[msg_key] = cls.get(msg_key)
        else:
            # needed for tests
            messages = {key.replace(f"{cls.prefix}", ""): current_cache.get(key) for key in current_cache.cache._cache}

        return messages
