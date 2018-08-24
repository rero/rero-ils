# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Jinja filters."""

import json

import babel
import dateparser
from flask_babelex import gettext as _

from .modules.items.models import ItemStatus


def format_date_filter(date_str, format='medium', locale='en'):
    """Format the date."""
    form_date = dateparser.parse(str(date_str))
    if format == 'full':
        format = "EEEE, d. MMMM y"
    elif format == 'medium':
        format = "EE dd.MM.y"
    elif format == 'medium_date':
        format = "dd MMMM y"
    elif format == 'short_date':
        format = "dd.MM.y"
    elif format == 'timestamp':
        format = "dd.MM.y HH:mm"
    return babel.dates.format_datetime(form_date, format, locale=locale)


def to_pretty_json(value):
    """Pretty json format."""
    return json.dumps(
        value,
        sort_keys=True,
        indent=4,
        separators=(',', ': '),
        ensure_ascii=False,
    )


def item_status_text(item, format='medium', locale='en'):
    """Text for item status."""
    if item.available:
        text = _('available')
        if item.get('item_type') == "on_site_consultation":
            text += ' ({0})'.format(_("on_site consultation"))
    else:
        text = _('not available')
        if item.status == ItemStatus.ON_LOAN:
            due_date = format_date_filter(
                item.get_item_end_date(),
                format=format,
                locale=locale
            )
            text += ' ({0} {1})'.format(_('due until'), due_date)
        elif item.number_of_item_requests() > 0:
            text += ' ({0})'.format(_('requested'))
        elif item.status == ItemStatus.IN_TRANSIT:
            text += ' ({0})'.format(_(ItemStatus.IN_TRANSIT))
    return text
