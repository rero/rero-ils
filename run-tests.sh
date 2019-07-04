#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# RERO ILS
# Copyright (C) 2019 RERO
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
