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

"""Utilities for rero-ils editor."""

from flask import current_app, url_for
from invenio_indexer.api import RecordIndexer

from .babel_extractors import translate


def get_schema(schema):
    """Return jsonschemas dictionary."""
    ext = current_app.extensions.get('invenio-jsonschemas')
    keys = current_app.config['RERO_ILS_BABEL_TRANSLATE_JSON_KEYS']
    ext.get_schema.cache_clear()
    return translate(ext.get_schema(schema), keys=keys)


def get_schema_url(schema):
    """Return jsonschemas url path."""
    ext = current_app.extensions.get('invenio-jsonschemas')
    return ext.path_to_url(schema)


def delete_record(record_type, record_class, pid):
    """Remove a record from the db and the index and his corresponding pid."""
    record = record_class.get_record_by_pid(pid)
    record.delete(delindex=True)
    record.dbcommit(reindex=False)
    RecordIndexer().client.indices.flush()
    _next = url_for('%s.index_view' % record_type)
    return _next, record.pid


def save_record(data, record_type, record_class, parent_pid=None):
    """Save a record into the db and index it."""
    # load and clean dirty data provided by angular-schema-form
    pid = data.get('pid')
    data = clean_dict_keys(data)
    # update an existing record
    if pid:
        record = record_class.get_record_by_pid(pid)
        record.update(data, dbcommit=False, reindex=False)
    # create a new record
    else:
        # create a new record
        record = record_class.create(data, dbcommit=False)
    record.dbcommit(reindex=True)
    RecordIndexer().client.indices.flush()

    _next = url_for('invenio_records_ui.%s' % record_type,
                    pid_value=record.pid)

    return _next, record.pid


def clean_dict_keys(data):
    """Remove key having useless values."""
    # return a new list with defined value only
    if isinstance(data, list):
        to_return = []
        for item in data:
            if item is False:
                to_return.append(item)
            else:
                tmp = clean_dict_keys(item)
                if tmp:
                    to_return.append(tmp)
        return to_return

    # return a new dict with defined value only
    if isinstance(data, dict):
        to_return = {}
        for k, v in data.items():
            if v is False:
                to_return[k] = v
            else:
                tmp = clean_dict_keys(v)
                if tmp:
                    to_return[k] = tmp
        return to_return

    return data


def remove_pid(editor_options, pid_value):
    """Remove PID in the editor option for new record."""
    for option in reversed(editor_options):
        if isinstance(option, str):
            if option == pid_value:
                editor_options.remove(option)
        if isinstance(option, dict):
            items = option.get('items')
            if option.get('key') == pid_value:
                editor_options.remove(option)
            elif isinstance(items, list):
                new_items = remove_pid(items, pid_value)
                if new_items:
                    option['items'] = new_items
                else:
                    editor_options.remove(option)
        if isinstance(option, list):
            editor_options = remove_pid(option, pid_value)
    return editor_options
