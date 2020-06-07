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

# Poetry is a mandatory condition to launch this program!
if [[ -z "${VIRTUAL_ENV}" ]]; then
  error_msg+exit "Error - Launch this script via poetry command:\n\tpoetry run ${PROGRAM}"
fi

if [ $# -eq 0 ]
    then
        grep -r fuzzy rero_ils/translations
        if [ $? -eq 0 ]
        then
            error_msg+exit "Error: fuzzy tranlations!"
        fi

        set -e
        safety check
        flask utils check_json tests/data rero_ils/modules data
        flask utils check_license check_license_config.yml
        info_msg "Test pydocstyle:"
        pydocstyle rero_ils tests docs
        info_msg "Test isort:"
        isort -rc -c -df
        info_msg "Test useless imports:"
        autoflake -c -r \
          --remove-all-unused-imports \
          --ignore-init-module-imports . \
          &> /dev/null || \
          error_msg+exit "\nUse this command to check imports: \n\tautoflake --remove-all-unused-imports -r --ignore-init-module-imports .\n"

        # info_msg "Check-manifest:"
        # TODO: check if this is required when rero-ils will be published
        # check-manifest --ignore ".travis-*,docs/_build*"
        info_msg "Sphinx-build:"
        sphinx-build -qnNW docs docs/_build/html
        info_msg "Tests:"
        # invenio utils set_test_static_folder -v
        poetry run tests
fi
if [ "$1" = "external" ]
    then
        export PYTEST_ADDOPTS="--cov-append -m "external""

        info_msg "External tests:"
        test
fi

success_msg "Perfect ${PROGRAM}! See you soon…"
exit 0
