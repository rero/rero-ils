# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""rero21 ils data module."""

from __future__ import absolute_import, print_function

import json


def pretty_json_dump(iterator):
    """Dump JSON from iteraror."""
    return json.dumps(list(iterator), indent=4)
