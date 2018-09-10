#!/usr/bin/env bash
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


grep -r fuzzy rero_ils/translations


if [ $? -eq 0 ]
then
    echo "Error: fuzzy tranlations!"
    exit 1
fi

set -e

# TODO: remove exception once is fixed
pipenv check -i 36437
pipenv run flask utils check_json
pipenv run pydocstyle rero_ils tests docs
pipenv run isort -rc -c -df
pipenv run check-manifest --ignore ".travis-*,docs/_build*"
pipenv run sphinx-build -qnNW docs docs/_build/html

# workaround see: https://github.com/inveniosoftware/invenio-app/issues/31
FLASK_DEBUG=False pipenv run test
#pipenv run test
