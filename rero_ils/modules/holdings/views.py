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

"""Blueprint used for loading templates."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import Blueprint, current_app, flash, jsonify, redirect, \
    render_template, url_for
from flask_babelex import gettext as _
from flask_login import current_user
from invenio_records_ui.signals import record_viewed

from .api import Holding
from ..documents.api import Document
from ...permissions import request_item_permission


def holding_view_method(pid, record, template=None, **kwargs):
    r"""Display default view.

    Sends record_viewed signal and renders template.
    :param pid: PID object.
    :param record: Record object.
    :param template: Template to render.
    :param \*\*kwargs: Additional view arguments based on URL rule.
    :returns: The rendered template.
    """
    record_viewed.send(
        current_app._get_current_object(), pid=pid, record=record
    )
    document = Document.get_record_by_pid(
        record.replace_refs()['document']['pid'])
    holding = record.replace_refs()
    return render_template(
        template, pid=pid, record=record, document=document)


blueprint = Blueprint(
    'holding',
    __name__,
    url_prefix='/holding',
    template_folder='templates',
    static_folder='static',
)
