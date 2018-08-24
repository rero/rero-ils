# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent identifier minters."""

from __future__ import absolute_import, print_function, unicode_literals


def id_minter(record_uuid, data, provider, pid_key='pid', object_type='rec'):
    """RERIOLS Organisationid minter."""
    assert pid_key not in data
    provider = provider.create(
        object_type=object_type,
        object_uuid=record_uuid
    )
    pid = provider.pid
    data[pid_key] = pid.pid_value

    return pid
