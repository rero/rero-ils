# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent identifier fetchers."""


from __future__ import absolute_import, print_function

from collections import namedtuple

FetchedPID = namedtuple('FetchedPID', ['provider', 'pid_type', 'pid_value'])
"""A pid fetcher."""


def id_fetcher(record_uuid, data, provider, pid_key='pid'):
    """Fetch a Organisation record's identifiers.

    :param record_uuid: The record UUID.
    :param data: The record metadata.
    :returns: A :data:`reroils_app.modules.fetchers.FetchedPID` instance.
    """
    return FetchedPID(
        provider=provider,
        pid_type=provider.pid_type,
        pid_value=data[pid_key]
    )
