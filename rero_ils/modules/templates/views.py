# SPDX-FileCopyrightText: Fondation RERO+
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Blueprint used for loading templates."""

from flask import Blueprint

blueprint = Blueprint(
    "templates",
    __name__,
    url_prefix="/template",
    template_folder="templates",
    static_folder="static",
)
