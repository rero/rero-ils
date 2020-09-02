# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
# Copyright (C) 2020 UCLOUVAIN
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

"""Facets and factories for result aggregation."""

from __future__ import absolute_import, print_function

from flask import current_app, request
from invenio_i18n.ext import current_i18n


def i18n_facets_factory(search, index):
    """Add a i18n facets to search query.

    It's possible to select facets which should be added to query
    by passing their name in `facets` parameter.

    :param search: Basic search object.
    :param index: Index name.
    :returns: the new search object.
    """
    facets_config = current_app.config['RECORDS_REST_FACETS'].get(index, {})
    # i18n Aggregations.
    for name, agg in facets_config.get("i18n_aggs", {}).items():
        i18n_agg = agg.get(
            request.args.get("lang", current_i18n.language),
            agg.get(current_app.config.get('BABEL_DEFAULT_LANGUAGE'))
        )
        search.aggs[name] = i18n_agg if not callable(i18n_agg) \
            else i18n_agg()
    return search
