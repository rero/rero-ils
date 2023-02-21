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

"""Entities utilities."""

from __future__ import absolute_import, print_function

from flask import current_app


def get_entity_localized_value(entity, key, language):
    """Get the first localized value for given key among MEF source list.

    :param entity: Entity data.
    :param key: Key to find a translated form.
    :param language: Language to use.
    :returns: Value from key in language if found otherwise the value of key.
    """
    order = current_app.config.get('RERO_ILS_AGENTS_LABEL_ORDER', [])
    source_order = order.get(language, order.get(order['fallback'], []))
    for source in source_order:
        if value := entity.get(source, {}).get(key):
            return value
    return entity.get(key)
