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
SCRIPT_PATH=$(dirname "$0")

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

function pretests () {
  # TODO: find out why we have following error:
  # | pipenv                     | 2018.11.2 | <2020.5.28               | 38334    |
  safety check --ignore 38334
  info_msg "Check json:"
  flask utils check_json tests/data rero_ils/modules data
  info_msg "Check license:"
  flask utils check_license check_license_config.yml
  info_msg "Test pydocstyle:"
  pydocstyle rero_ils tests docs
  info_msg "Test isort:"
  isort --check-only --diff "${SCRIPT_PATH}"
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
}


# TODO: we have to test 3 folowing files:
# tests/conftest.py                                                                                                                                                                                                                                                 [  0%]
# tests/test_version.py                                                                                                                                                                                                                                            [  0%]
# tests/utils.py

function tests () {
  info_msg "Tests All:"
  unset PYTEST_ADDOPTS
  poetry run tests
}

function tests_api () {
  info_msg "Tests API:"
  unset PYTEST_ADDOPTS
  poetry run pytest ./tests/api
}
function tests_e2e () {
  info_msg "Tests E2E:"
  unset PYTEST_ADDOPTS
  poetry run pytest ./tests/e2e
}
function tests_scheduler () {
  info_msg "Tests Scheduler:"
  unset PYTEST_ADDOPTS
  poetry run pytest ./tests/scheduler
}
function tests_ui () {
  info_msg "Tests UI:"
  unset PYTEST_ADDOPTS
  poetry run pytest ./tests/ui
}
function tests_unit () {
  info_msg "Tests Unit:"
  unset PYTEST_ADDOPTS
  poetry run pytest ./tests/unit
}
function tests_other () {
  info_msg "Tests Other:"
  unset PYTEST_ADDOPTS
  poetry run pytest ./tests/conftest.py ./tests/test_version.py ./tests/utils.py
}

if [ $# -eq 0 ]
  then
    set -e
    pretests
    tests
fi
if [ "$1" = "other" ]
  then
    set -e
    pretests
    tests_other
fi
if [ "$1" = "api" ]
  then
    set -e
    tests_api
fi
if [ "$1" = "e2e" ]
  then
    set -e
    tests_e2e
fi
if [ "$1" = "scheduler" ]
  then
    set -e
    tests_scheduler
fi
if [ "$1" = "ui" ]
  then
    set -e
    tests_ui
fi
if [ "$1" = "unit" ]
  then
    set -e
    tests_unit
fi
if [ "$1" = "external" ]
  then
    export PYTEST_ADDOPTS="--cov-append -m "external""
    info_msg "External tests:"
    poetry run tests ${@:2}
fi


success_msg "Perfect ${PROGRAM}! See you soon…"
exit 0
