# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019-2022 RERO
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


import iso639
from flask import current_app
from flask_babel import gettext
from invenio_i18n.ext import current_i18n


def unique_list(data):
    """Unicity of list."""
    return list(dict.fromkeys(data))


def get_current_language():
    """Return the current selected locale."""
    return current_i18n.locale.language


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


def language_iso639_2to1(lang):
    """Convert a bibliographic language to alpha2.

    :param lang: bibliographic language code
    :returns: language (alpha2)
    """
    default_ln = current_i18n.babel.default_locale.language
    try:
        ln = iso639.to_iso639_1(lang)
    except iso639.NonExistentLanguageError:
        return default_ln
    supported_languages = [v[0] for v in current_i18n.get_languages()]
    return ln if ln in supported_languages else default_ln


def language_mapping(lang):
    """Language mapping.

    :param lang: bibliographic language code
    :returns: language mapping
    """
    return current_app.config.get('RERO_ILS_LANGUAGE_MAPPING', {})\
        .get(lang, lang)


class TranslatedList(list):
    """Translation on demand of elements in a list."""

    def __getitem__(self, item):
        """."""
        return gettext(list.__getitem__(self, item))
