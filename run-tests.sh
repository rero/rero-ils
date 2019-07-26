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

if [ $# -eq 0 ]
    then
        grep -r fuzzy rero_ils/translations
        if [ $? -eq 0 ]
        then
            echo "Error: fuzzy tranlations!"
            exit 1
        fi

        set -e
        pipenv check -i 36759
        pipenv run flask utils check_json tests rero_ils/modules data
        pipenv run pydocstyle rero_ils tests docs
        pipenv run isort -rc -c -df --skip ui

        # syntax check for typescript
        CWD=`pwd`
        cd ui; pipenv run npm run lint; cd -

        pipenv run check-manifest --ignore ".travis-*,docs/_build*,ui/node_modules*,rero_ils/static/js/rero_ils/ui*"
        pipenv run sphinx-build -qnNW docs docs/_build/html
        pipenv run test
fi
if [ "$1" = "external" ]
    then
        export PYTEST_ADDOPTS="--cov-append -m "external""

        pipenv run test
        exit 0
fi
