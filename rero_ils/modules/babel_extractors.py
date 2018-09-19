# -*- coding: utf-8 -*-
#
# This file is part of RERO ILS.
# Copyright (C) 2017 RERO.
#
# RERO ILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# RERO ILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RERO ILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""reroils translation json utils."""

import re

import six
from flask_babelex import gettext as _

KEY_VAL_REGEX = re.compile(r'"(.*?)"\s*:\s*"(.*?)"')


def translate(data, keys=['title']):
    """Translate strings in a data structure."""
    to_return = data
    if isinstance(data, dict):
        for k, v in six.iteritems(data):
            if k in keys and isinstance(v, str) and v:
                data[k] = _(v)
            else:
                translate(v, keys)
    if isinstance(data, list):
        for v in data:
            translate(v, keys)
    return to_return


def extract(fileobj, keys=['title']):
    """Extract translation from a json file."""
    translations = []
    line = 1
    for v in fileobj:
        for match in KEY_VAL_REGEX.finditer(v.decode('utf-8')):
            k_match, v_match = match.groups()
            # if k_match in keys and v_match:
            for regexkey in keys:
                if re.match(regexkey, k_match):
                    translations.append((line, 'gettext', v_match, []))
                    continue
        line += 1
    return translations


def extract_json(fileobj, keywords, comment_tags, options):
    """Extract messages from JSON files.

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (optional)
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``
    """
    keys_to_translate = eval(options.get('keys_to_translate', "['title']"))
    return extract(fileobj, keys_to_translate)
