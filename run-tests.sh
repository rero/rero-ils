#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

echo $VIRTUAL_ENV
set -
flask utils check_json
pydocstyle reroils_app tests docs
isort -rc -c -df

set +e
grep -r fuzzy reroils_app/translations
if [ $? -eq 0 ]
then
    echo "Error: fuzzy tranlations!"
    exit 1
fi

set -e
check-manifest --ignore ".travis-*,docs/_build*"
sphinx-build -qnNW docs docs/_build/html
python setup.py test
