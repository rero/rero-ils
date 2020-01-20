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

# COLORS for messages
NC='\033[0m'                    # Default color
INFO_COLOR='\033[1;97;44m'      # Bold + white + blue background
SUCCESS_COLOR='\033[1;97;42m'   # Bold + white + green background
ERROR_COLOR='\033[1;97;41m'     # Bold + white + red background

PROGRAM=`basename $0`

# MESSAGES
msg() {
  echo -e "${1}" 1>&2
}
# Display a colored message
# More info: https://misc.flogisoft.com/bash/tip_colors_and_formatting
# $1: choosen color
# $2: title
# $3: the message
colored_msg() {
  msg "${1}[${2}]: ${3}${NC}"
}

info_msg() {
  colored_msg "${INFO_COLOR}" "INFO" "${1}"
}

error_msg() {
  colored_msg "${ERROR_COLOR}" "ERROR" "${1}"
}

error_msg+exit() {
    error_msg "${1}" && exit 1
}

success_msg() {
  colored_msg "${SUCCESS_COLOR}" "SUCCESS" "${1}"
}

# Displays program name
msg "PROGRAM: ${PROGRAM}"

# compile json files (resolve $ref)
pipenv run invenio utils compile_json ./rero_ils/modules/documents/jsonschemas/documents/document-minimal-v0.0.1_src.json -o ./rero_ils/modules/documents/jsonschemas/documents/document-minimal-v0.0.1.json
pipenv run invenio utils compile_json ./rero_ils/modules/documents/jsonschemas/documents/document-v0.0.1_src.json -o ./rero_ils/modules/documents/jsonschemas/documents/document-v0.0.1.json

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
        info_msg "Test pydocstyle:"
        pipenv run pydocstyle rero_ils tests docs
        info_msg "Test isort:"
        pipenv run isort -rc -c -df --skip ui
        echo -e ${GREEN}Test useless imports:${NC}
        pipenv run autoflake -c -r \
          --remove-all-unused-imports \
          --exclude ui \
          --ignore-init-module-imports . \
          &> /dev/null || \
          error_msg+exit "\nUse this command to check imports: \n\tautoflake --remove-all-unused-imports -r --exclude ui --ignore-init-module-imports .\n"

        # syntax check for typescript
        info_msg "Syntax check for typescript:"
        CWD=`pwd`

        info_msg "Check-manifest:"
        pipenv run check-manifest --ignore ".travis-*,docs/_build*"
        info_msg "Sphinx-build:"
        pipenv run sphinx-build -qnNW docs docs/_build/html
        info_msg "Tests:"
        pipenv run test
fi
if [ "$1" = "external" ]
    then
        export PYTEST_ADDOPTS="--cov-append -m "external""

        info_msg "External tests:"
        pipenv run test
fi

success_msg "Perfect ${PROGRAM}! See you soon…"
exit 0
