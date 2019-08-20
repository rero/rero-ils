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
# along with this program. If not, see <http://www.gnu.org/licenses/>.

RED='\033[0;31m'
GREEN='\033[0;0;32m'
NC='\033[0m' # No Color

if [ $# -eq 0 ]
    then
        grep -r fuzzy rero_ils/translations
        if [ $? -eq 0 ]
        then
            echo -e ${RED}"Error: fuzzy tranlations!"${NC}
            exit 1
        fi

        set -e
        pipenv check -i 36759
        pipenv run flask utils check_json tests rero_ils/modules data
        pipenv run flask utils check_license check_license_config.yml
        echo -e ${GREEN}Test pydocstyle:${NC}
        pipenv run pydocstyle rero_ils tests docs
        echo -e ${GREEN}Test isort:${NC}
        pipenv run isort -rc -c -df --skip ui

        # syntax check for typescript
        echo -e ${GREEN}Syntax check for typescript:${NC}
        CWD=`pwd`
        cd ui; pipenv run npm run lint; cd -

        echo -e ${GREEN}Check-manifest:${NC}
        pipenv run check-manifest --ignore ".travis-*,docs/_build*,ui/node_modules*,rero_ils/static/js/rero_ils/ui*"
        echo -e ${GREEN}Sphinx-build:${NC}
        pipenv run sphinx-build -qnNW docs docs/_build/html
        echo -e ${GREEN}Tests:${NC}
        pipenv run test
fi
if [ "$1" = "external" ]
    then
        export PYTEST_ADDOPTS="--cov-append -m "external""

        echo -e ${GREEN}External tests:${NC}
        pipenv run test
        exit 0
fi
