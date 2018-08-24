# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 RERO.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Blueprint used for loading templates.

The sole purpose of this blueprint is to ensure that Invenio can find the
templates and static files located in the folders of the same names next to
this file.
"""

from __future__ import absolute_import, print_function

from flask import Blueprint, jsonify, render_template
from flask_babelex import gettext as _
from flask_login import current_user, login_required
from flask_menu import register_menu
from werkzeug.exceptions import NotFound

from .api import Patron
from .utils import structure_document, user_has_patron

blueprint = Blueprint(
    'patrons',
    __name__,
    url_prefix='/patrons',
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/profile')
@login_required
@register_menu(
    blueprint,
    'main.profile',
    _('%(icon)s Profile', icon='<i class="fa fa-user fa-fw"></i>'),
    visible_when=user_has_patron
)
def profile():
    """Patron Profile Page."""
    patron = Patron.get_patron_by_user(current_user)
    if patron is None:
        raise NotFound()
    documents = patron.get_borrowed_documents()
    loans, pendings = structure_document(documents, patron.get('barcode'))

    return render_template(
        'reroils_app/patron_profile.html',
        record=patron,
        loans=loans,
        pendings=pendings
    )


@blueprint.route('/logged_user', methods=['GET'])
@login_required
def logger_user():
    """Current logged user informations in JSON."""
    patron = Patron.get_patron_by_user(current_user)
    if patron is None:
        raise NotFound()
    return jsonify(patron.dumps())


@blueprint.app_template_filter('get_patron_from_barcode')
def get_patron_from_barcode(value):
    """Get patron from barcode."""
    return Patron.get_patron_by_barcode(value)
