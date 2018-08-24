# -*- coding: utf-8 -*-
#
# Copyright (C) 2018 RERO.
#
# reroils-app is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Permissions for this module."""


from flask_login import current_user
from flask_principal import RoleNeed
from invenio_access.permissions import DynamicPermission

request_item_permission = DynamicPermission(RoleNeed('patrons'))


def can_request(user=None):
    """User can request items."""
    if not user:
        user = current_user
    return user.is_authenticated and request_item_permission.can()
