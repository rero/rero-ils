# -*- coding: utf-8 -*-
#
# This file is part of REROILS.
# Copyright (C) 2017 RERO.
#
# REROILS is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# REROILS is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with REROILS; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, RERO does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""JS/CSS bundles for theme.

You include one of the bundles in a page like the example below (using ``js``
bundle as an example):

.. code-block:: html

    {%- asset "invenio_theme.bundles:js" %}
    <script src="{{ASSET_URL}}"  type="text/javascript"></script>
    {%- end asset %}
"""

from __future__ import absolute_import, print_function

from flask_assets import Bundle
from invenio_assets import NpmBundle

profile_css = NpmBundle(
    'scss/reroils_app/patrons_profile.scss',
    filters='node-scss,cleancssurl',
    output='gen/style.patrons_profile.%(version)s.css',
)
"""Default style for partrons profile view."""

editor_js = Bundle(
    'js/reroils_app/patron-editor.js',
    filters='jsmin',
    output='gen/reroils_app.modules.patron-editor_js.%(version)s.js',
)
