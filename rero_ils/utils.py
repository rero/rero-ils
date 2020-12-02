# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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

"""Utilities functions for rero-ils."""


from flask import current_app
from invenio_i18n.ext import current_i18n


def unique_list(data):
    """Unicity of list."""
    return list(dict.fromkeys(data))


def get_current_language():
    """Return the current selected locale."""
    loc = current_i18n.locale
    return loc.language


def get_i18n_supported_languages():
    """Get defined languages from config.

    :returns: defined languages from config.
    """
    languages = [current_app.config.get('BABEL_DEFAULT_LANGUAGE')]
    i18n_languages = current_app.config.get('I18N_LANGUAGES')
    return languages + [ln[0] for ln in i18n_languages]


def remove_empties_from_dict(a_dict):
    """Remove empty values from a multi level dictionary.

    :return a cleaned dictionary.
    """
    new_dict = {}
    for k, v in a_dict.items():
        if isinstance(v, dict):
            v = remove_empties_from_dict(v)
        elif isinstance(v, list):
            v = [el for el in v if el]
        if v:
            new_dict[k] = v
    return new_dict or None
