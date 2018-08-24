# -*- coding: utf-8 -*-
#
# This file is part of organisations.
# Copyright (C) 2018 RERO.
#

"""Blueprint used for loading templates.

The sole purpose of this blueprint is to ensure that Invenio can find the
templates and static files located in the folders of the same names next to
this file.
"""

from __future__ import absolute_import, print_function

from flask import Blueprint

blueprint = Blueprint(
    'organisations',
    __name__,
    template_folder='templates',
    static_folder='static',
)
